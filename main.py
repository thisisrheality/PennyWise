import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QLabel, QPushButton, QStackedWidget
)

from database.database import Database
from features.dashboard.service import DashboardService
from features.dashboard.view import DashboardView
from features.transactions.service import TransactionService
from features.transactions.view import TransactionsView
from features.budget.service import BudgetService
from features.budget.view import BudgetView
from features.savings_account.service import SavingsService
from features.savings_account.view import SavingsView


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.setWindowTitle("PENNYWISE 🎈 • Personal Finance Tracker")
        self.resize(1200, 780)

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 28, 18, 28)
        sidebar_layout.setSpacing(10)

        app_title = QLabel("PENNYWISE 🎈")
        app_title.setObjectName("appTitle")
        app_sub = QLabel("Personal Finance Tracker")
        app_sub.setObjectName("appSubtitle")

        sidebar_layout.addWidget(app_title)
        sidebar_layout.addWidget(app_sub)
        sidebar_layout.addSpacing(20)

        self.nav_buttons = []
        nav_items = [
            ("📊  Overview", 0),
            ("💳  Transactions", 1),
            ("🎯  Budget Limits", 2),
            ("🎈  Savings Vault", 3)
        ]

        for label, index in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=index: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Engine Badge
        engine_badge = QLabel("🎈 SYSTEM ONLINE")
        engine_badge.setObjectName("statusBadge")
        sidebar_layout.addWidget(engine_badge)

        main_layout.addWidget(sidebar)

        # Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(16, 16, 16, 16)

        dash_service = DashboardService(db)
        trans_service = TransactionService(db)
        budget_service = BudgetService(db)
        savings_service = SavingsService(db)

        self.stack = QStackedWidget()

        self.dash_view = DashboardView(dash_service)
        self.trans_view = TransactionsView(trans_service, refresh_callback=self.refresh_all)
        self.budget_view = BudgetView(budget_service, refresh_callback=self.refresh_all)
        self.savings_view = SavingsView(savings_service, refresh_callback=self.refresh_all)

        self.stack.addWidget(self.dash_view)
        self.stack.addWidget(self.trans_view)
        self.stack.addWidget(self.budget_view)
        self.stack.addWidget(self.savings_view)

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_area)

        self.setCentralWidget(central_widget)
        self.switch_page(0)

    def switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def refresh_all(self) -> None:
        self.dash_view.refresh()
        self.trans_view.refresh()
        self.budget_view.refresh()
        self.savings_view.refresh()


def main():
    db = Database()
    db.create_tables()

    app = QApplication(sys.argv)
    app.setStyleSheet(Path(__file__).with_name("style.qss").read_text())

    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()