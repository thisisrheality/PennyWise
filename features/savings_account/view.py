from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .model import SavingsGoal


class SavingsView(QWidget):

    def __init__(self, service, refresh_callback=None):
        super().__init__()
        self.service = service
        self.refresh_callback = refresh_callback
        self.build_ui()
        self.refresh()

    def build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Header Bar
        hdr = QFrame()
        hdr.setObjectName("viewHeaderBar")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(12, 8, 12, 8)

        lbl_title = QLabel("SAVINGS VAULT")
        lbl_title.setObjectName("viewHeaderTitle")

        btn_add = QPushButton("+ New Goal")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self.add_goal)

        hdr_l.addWidget(lbl_title)
        hdr_l.addStretch()
        hdr_l.addWidget(btn_add)
        main_layout.addWidget(hdr, stretch=0)

        # Card Frame
        card = QFrame()
        card.setObjectName("cardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(12)

        # Action Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_deposit = QPushButton("Deposit")
        btn_deposit.setObjectName("secondaryButton")
        btn_deposit.clicked.connect(self.deposit)

        btn_withdraw = QPushButton("Withdraw")
        btn_withdraw.setObjectName("secondaryButton")
        btn_withdraw.clicked.connect(self.withdraw)

        btn_edit = QPushButton("Edit Goal")
        btn_edit.setObjectName("secondaryButton")
        btn_edit.clicked.connect(self.edit_goal)

        btn_delete = QPushButton("Delete Goal")
        btn_delete.setObjectName("dangerButton")
        btn_delete.clicked.connect(self.delete_goal)

        toolbar.addWidget(btn_deposit)
        toolbar.addWidget(btn_withdraw)
        toolbar.addWidget(btn_edit)
        toolbar.addStretch()
        toolbar.addWidget(btn_delete)

        c_layout.addLayout(toolbar)

        # Table Widget
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "GOAL NAME",
                "TARGET AMOUNT",
                "CURRENT SAVED",
                "GOAL PROGRESS",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        c_layout.addWidget(self.table)
        main_layout.addWidget(card, stretch=1)

    def get_selected_goal_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select a savings goal row from the table first.",
            )
            return None
        return int(self.table.item(row, 0).text())

    def add_goal(self):
        title, ok1 = QInputDialog.getText(self, "New Savings Goal", "Goal Title:")
        if not ok1 or not title.strip():
            return
        target_str, ok2 = QInputDialog.getText(
            self, "New Savings Goal", "Target Amount (₱):"
        )
        if not ok2 or not target_str.strip():
            return

        try:
            target = float(target_str)
            g = SavingsGoal(title=title.strip(), target_amount=target)
            self.service.add_goal(g)
            self.refresh()
            if self.refresh_callback:
                self.refresh_callback()
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Input", "Please enter a valid numeric target."
            )

    def deposit(self):
        goal_id = self.get_selected_goal_id()
        if goal_id is None:
            return

        amt, ok = QInputDialog.getDouble(
            self,
            "Deposit Funds",
            "Amount to deposit into goal (₱):",
            min=1.0,
            decimals=2,
        )
        if ok:
            try:
                self.service.deposit(goal_id, amt)
                self.refresh()
                if self.refresh_callback:
                    self.refresh_callback()
            except ValueError as err:
                QMessageBox.warning(self, "Deposit Error", str(err))

    def withdraw(self):
        goal_id = self.get_selected_goal_id()
        if goal_id is None:
            return

        amt, ok = QInputDialog.getDouble(
            self,
            "Withdraw Funds",
            "Amount to withdraw from goal (₱):",
            min=1.0,
            decimals=2,
        )
        if ok:
            try:
                self.service.withdraw(goal_id, amt)
                self.refresh()
                if self.refresh_callback:
                    self.refresh_callback()
            except ValueError as err:
                QMessageBox.warning(self, "Withdrawal Error", str(err))

    def edit_goal(self):
        goal_id = self.get_selected_goal_id()
        if goal_id is None:
            return

        goals = self.service.get_goals()
        goal = next((g for g in goals if g.id == goal_id), None)
        if not goal:
            return

        new_title, ok1 = QInputDialog.getText(
            self, "Edit Goal", "Goal Title:", text=goal.title
        )
        if not ok1 or not new_title.strip():
            return

        new_target, ok2 = QInputDialog.getDouble(
            self,
            "Edit Goal",
            "Target Amount (₱):",
            value=goal.target_amount,
            min=1.0,
            decimals=2,
        )
        if not ok2:
            return

        goal.title = new_title.strip()
        goal.target_amount = new_target
        self.service.update_goal(goal)
        self.refresh()
        if self.refresh_callback:
            self.refresh_callback()

    def delete_goal(self):
        goal_id = self.get_selected_goal_id()
        if goal_id is None:
            return

        goals = self.service.get_goals()
        goal = next((g for g in goals if g.id == goal_id), None)
        if not goal:
            return

        msg = f"Are you sure you want to delete the goal '{goal.title}'?"
        if goal.current_amount > 0:
            msg += f"\n\nRemaining savings of ₱{goal.current_amount:,.2f} will be refunded back to your net balance."

        reply = QMessageBox.question(
            self,
            "Confirm Goal Deletion",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            refunded = self.service.delete_goal(goal_id)
            if refunded > 0:
                QMessageBox.information(
                    self,
                    "Funds Refunded",
                    f"₱{refunded:,.2f} was refunded to your net balance.",
                )
            self.refresh()
            if self.refresh_callback:
                self.refresh_callback()

    def refresh(self):
        goals = self.service.get_goals()
        self.table.setRowCount(len(goals))

        for row, g in enumerate(goals):
            pct = (
                int((g.current_amount / g.target_amount) * 100)
                if g.target_amount > 0
                else 0
            )
            pct_clamped = min(100, pct)

            self.table.setItem(row, 0, QTableWidgetItem(str(g.id)))
            self.table.setItem(row, 1, QTableWidgetItem(g.title))
            self.table.setItem(
                row, 2, QTableWidgetItem(f"₱{g.target_amount:,.2f}")
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(f"₱{g.current_amount:,.2f}")
            )

            pbar = QProgressBar()
            pbar.setValue(pct_clamped)
            pbar.setFixedHeight(18)
            pbar.setTextVisible(True)
            pbar.setFormat(f"🎉 Completed ({pct}%)" if pct >= 100 else f"{pct}% Saved")
            pbar.setObjectName("pbarSuccess" if pct >= 100 else "pbarNormal")

            self.table.setCellWidget(row, 4, pbar)