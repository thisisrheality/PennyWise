from database.database import Database
from .model import Budget

class BudgetRepository:
    def __init__(self, database: Database):
        self.database = database

    def set_budget(self, b: Budget) -> Budget:
        with self.database.connect() as conn:
            conn.execute(
                "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
                "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
                (b.category, b.monthly_limit),
            )
        return b

    def list_all(self) -> list[Budget]:
        with self.database.connect() as conn:
            rows = conn.execute("SELECT id, category, monthly_limit FROM budgets").fetchall()
        return [Budget(id=row[0], category=row[1], monthly_limit=row[2]) for row in rows]