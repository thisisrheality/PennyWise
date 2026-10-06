from database.database import Database
from .model import Budget


class BudgetService:

    def __init__(self, database: Database):
        self.database = database

    def set_budget(self, budget: Budget) -> None:
        if budget.monthly_limit <= 0:
            raise ValueError("Budget limit must be greater than zero.")
        if not budget.category.strip():
            raise ValueError("Category cannot be empty.")
        if not budget.month.strip():
            raise ValueError("Month must be selected.")

        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO budgets (category, monthly_limit, month)
                VALUES (?, ?, ?)
                ON CONFLICT(category, month) DO UPDATE SET
                    monthly_limit = excluded.monthly_limit
                """,
                (
                    budget.category.strip(),
                    budget.monthly_limit,
                    budget.month.strip(),
                ),
            )

    def get_budgets_for_month(self, month: str) -> list[dict]:
        """Returns budget target, current spent amount from transactions, and remaining balance for a specific month."""
        with self.database.connect() as conn:
            # Get defined budgets for selected month
            budgets = conn.execute(
                "SELECT id, category, monthly_limit, month FROM budgets WHERE month = ?",
                (month,),
            ).fetchall()

            result = []
            for b_id, cat, limit, m in budgets:
                # Calculate total expenses for this category in this month
                spent = (
                    conn.execute(
                        """
                    SELECT SUM(amount) FROM transactions 
                    WHERE type = 'Expense' 
                      AND LOWER(category) = LOWER(?) 
                      AND strftime('%Y-%m', date) = ?
                    """,
                        (cat, m),
                    ).fetchone()[0]
                    or 0.0
                )

                remaining = limit - spent
                result.append(
                    {
                        "id": b_id,
                        "category": cat,
                        "monthly_limit": limit,
                        "spent": spent,
                        "remaining": remaining,
                        "month": m,
                    }
                )

            return result

    def delete_budget(self, budget_id: int) -> None:
        with self.database.connect() as conn:
            conn.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))