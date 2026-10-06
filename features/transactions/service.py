from database.database import Database
from .model import Transaction
from .repository import TransactionRepository

class TransactionService:
    def __init__(self, database: Database):
        self.repository = TransactionRepository(database)

    def add_transaction(self, t: Transaction) -> Transaction:
        return self.repository.add(t)

    def get_all_transactions(self) -> list[Transaction]:
        return self.repository.list_all()

    def update_transaction(self, t: Transaction) -> None:
        self.repository.update(t)

    def delete_transaction(self, trans_id: int) -> None:
        self.repository.delete(trans_id)