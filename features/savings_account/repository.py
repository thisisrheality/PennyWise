from database.database import Database
from .model import SavingsGoal

class SavingsRepository:
    def __init__(self, database: Database):
        self.database = database

    # CREATE
    def add(self, goal: SavingsGoal) -> SavingsGoal:
        with self.database.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO savings_goals (title, target_amount, current_amount) VALUES (?, ?, ?)",
                (goal.title, goal.target_amount, goal.current_amount)
            )
            goal.id = cursor.lastrowid
        return goal

    # READ
    def list_all(self) -> list[SavingsGoal]:
        with self.database.connect() as conn:
            rows = conn.execute("SELECT id, title, target_amount, current_amount FROM savings_goals").fetchall()
        return [
            SavingsGoal(id=row[0], title=row[1], target_amount=row[2], current_amount=row[3])
            for row in rows
        ]

    # UPDATE
    def update(self, goal: SavingsGoal) -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE savings_goals SET title = ?, target_amount = ?, current_amount = ? WHERE id = ?",
                (goal.title, goal.target_amount, goal.current_amount, goal.id)
            )

    # DELETE
    def delete(self, goal_id: int) -> None:
        with self.database.connect() as conn:
            conn.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))