from datetime import datetime
from typing import Optional

from database.database import Database
from .model import SavingsGoal
from .repository import SavingsRepository


class SavingsService:

    def __init__(self, database: Database):
        self.database = database
        self.repository = SavingsRepository(database)

    def add_goal(self, goal: SavingsGoal) -> SavingsGoal:
        return self.repository.add(goal)

    def get_goals(self) -> list[SavingsGoal]:
        return self.repository.list_all()

    def update_goal(self, goal: SavingsGoal) -> None:
        self.repository.update(goal)

    from datetime import datetime

    def deposit(
            self, goal_id: int, amount: float, date_str: str | None = None
    ) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        goals = self.repository.list_all()
        goal = next((g for g in goals if g.id == goal_id), None)
        if not goal:
            raise ValueError("Savings goal not found.")

        goal.current_amount += amount
        self.repository.update(goal)

        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO transactions (date, type, category, amount, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    date_str,
                    "Savings Deposit",
                    "Savings",
                    amount,
                    f"Deposit to: {goal.title}",
                ),
            )
            conn.commit()

    def withdraw(
        self, goal_id: int, amount: float, date_str: Optional[str] = None
    ) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        goals = self.repository.list_all()
        goal = next((g for g in goals if g.id == goal_id), None)
        if not goal:
            raise ValueError("Savings goal not found.")

        if amount > goal.current_amount:
            raise ValueError(
                f"Cannot withdraw ₱{amount:,.2f}. Available balance in"
                f" '{goal.title}' is ₱{goal.current_amount:,.2f}."
            )

        goal.current_amount -= amount
        self.repository.update(goal)

        # Returns funds back to liquid balance
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO transactions (type, category, amount, description, date) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Savings Withdrawal",
                    "Savings",
                    amount,
                    f"Withdrawal from: {goal.title}",
                    date_str,
                ),
            )
            conn.commit()

    def delete_goal(
        self, goal_id: int, date_str: Optional[str] = None
    ) -> float:
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        goals = self.repository.list_all()
        goal = next((g for g in goals if g.id == goal_id), None)
        if not goal:
            return 0.0

        refund_amount = goal.current_amount
        if refund_amount > 0:
            with self.database.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO transactions (type, category, amount, description, date) 
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        "Savings Refund",
                        "Savings",
                        refund_amount,
                        f"Refund from deleted goal: {goal.title}",
                        date_str,
                    ),
                )
                conn.commit()

        self.repository.delete(goal_id)
        return refund_amount