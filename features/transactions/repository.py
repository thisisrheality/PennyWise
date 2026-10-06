from database.database import Database
from .model import Transaction


class TransactionRepository:

    def __init__(self, database: Database):
        self.database = database

    # CREATE
    def add(self, t: Transaction) -> Transaction:
        with self.database.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO transactions (type, category, amount, description, date) VALUES (?, ?, ?, ?, ?)",
                (t.trans_type, t.category, t.amount, t.description, t.date),
            )
            t.id = cursor.lastrowid
        return t

    # READ
    def list_all(self) -> list[Transaction]:
        with self.database.connect() as conn:
            rows = conn.execute(
                "SELECT id, type, category, amount, description, date FROM transactions ORDER BY date DESC, id DESC"
            ).fetchall()
        return [
            Transaction(
                id=row[0],
                trans_type=row[1],
                category=row[2],
                amount=row[3],
                description=row[4],
                date=row[5],
            )
            for row in rows
        ]

    # UPDATE
    def update(self, t: Transaction) -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE transactions SET type = ?, category = ?, amount = ?, description = ?, date = ? WHERE id = ?",
                (
                    t.trans_type,
                    t.category,
                    t.amount,
                    t.description,
                    t.date,
                    t.id,
                ),
            )

    # DELETE
    def delete(self, trans_id: int) -> None:
        with self.database.connect() as conn:
            conn.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))