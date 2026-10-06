from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .model import Transaction


class TransactionsView(QWidget):

    def __init__(self, service, refresh_callback=None):
        super().__init__()
        self.service = service
        self.refresh_callback = refresh_callback
        self.all_transactions = []
        self.editing_id = None
        self.build_ui()
        self.refresh()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header Bar
        hdr = QFrame()
        hdr.setObjectName("viewHeaderBar")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(12, 8, 12, 8)

        lbl_title = QLabel("TRANSACTIONS LOG")
        lbl_title.setObjectName("viewHeaderTitle")

        hdr_l.addWidget(lbl_title)
        hdr_l.addStretch()
        layout.addWidget(hdr, stretch=0)

        # Card Frame
        card = QFrame()
        card.setObjectName("cardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(12)

        # Search & Period Filter Bar
        filter_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search notes or category...")
        self.search_input.textChanged.connect(self.apply_filters)

        self.period_filter = QComboBox()
        self.period_filter.addItems([
            "All Time",
            "This Month",
            "Last Month",
            "This Year"
        ])
        self.period_filter.currentTextChanged.connect(self.apply_filters)

        filter_bar.addWidget(self.search_input, stretch=2)
        filter_bar.addWidget(self.period_filter, stretch=1)
        c_layout.addLayout(filter_bar)

        # Form Bar
        form_bar = QHBoxLayout()
        form_bar.setSpacing(8)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setFixedWidth(110)

        self.type_input = QComboBox()
        self.type_input.addItems(["Expense", "Income"])
        self.type_input.setFixedWidth(100)

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Category")
        self.category_input.setFixedWidth(130)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount (₱)")
        self.amount_input.setFixedWidth(100)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Notes / Details")

        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.clicked.connect(self.save_transaction)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.clicked.connect(self.delete_transaction)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setObjectName("secondaryButton")
        self.btn_clear.clicked.connect(self.clear_form)

        form_bar.addWidget(self.date_input)
        form_bar.addWidget(self.type_input)
        form_bar.addWidget(self.category_input)
        form_bar.addWidget(self.amount_input)
        form_bar.addWidget(self.desc_input, stretch=1)
        form_bar.addWidget(self.btn_save)
        form_bar.addWidget(self.btn_delete)
        form_bar.addWidget(self.btn_clear)

        c_layout.addLayout(form_bar)

        # Table Widget
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "DATE", "TYPE", "CATEGORY", "AMOUNT", "NOTES"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_row_selected)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(3, 130)

        c_layout.addWidget(self.table)
        layout.addWidget(card, stretch=1)

    def is_savings_transaction(self, trans_type: str) -> bool:
        return trans_type in [
            "Savings Deposit",
            "Savings Withdrawal",
            "Savings Refund",
        ]

    def save_transaction(self):
        try:
            amt = float(self.amount_input.text() or 0)
            if amt <= 0:
                raise ValueError("Amount must be greater than zero.")

            cat = self.category_input.text().strip()
            if not cat:
                raise ValueError("Category cannot be empty.")

            date_str = self.date_input.date().toString("yyyy-MM-dd")

            t = Transaction(
                trans_type=self.type_input.currentText(),
                category=cat,
                amount=amt,
                description=self.desc_input.text().strip(),
                date=date_str,
                id=self.editing_id,
            )

            if self.editing_id is None:
                self.service.add_transaction(t)
            else:
                self.service.update_transaction(t)

            self.clear_form()
            self.refresh()
            if self.refresh_callback:
                self.refresh_callback()

        except ValueError as err:
            QMessageBox.warning(self, "Invalid Input", str(err))

    def on_row_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return

        row = self.table.currentRow()
        trans_id = int(self.table.item(row, 0).text())
        transaction = next(
            (t for t in self.all_transactions if t.id == trans_id), None
        )

        if not transaction:
            return

        if self.is_savings_transaction(transaction.trans_type):
            QMessageBox.information(
                self,
                "Action Locked",
                "Savings transactions are managed automatically inside the Savings Vault tab.",
            )
            self.clear_form()
            return

        self.editing_id = transaction.id
        self.type_input.setCurrentText(transaction.trans_type)
        self.category_input.setText(transaction.category)
        self.amount_input.setText(str(transaction.amount))
        self.desc_input.setText(transaction.description)

        if transaction.date:
            qdate = QDate.fromString(transaction.date, "yyyy-MM-dd")
            if qdate.isValid():
                self.date_input.setDate(qdate)

        self.btn_save.setText("Update")

    def delete_transaction(self):
        row = self.table.currentRow()
        if row < 0 or self.editing_id is None:
            QMessageBox.warning(
                self, "Select Row", "Please select a transaction to delete."
            )
            return

        transaction = next(
            (t for t in self.all_transactions if t.id == self.editing_id), None
        )

        if not transaction or self.is_savings_transaction(transaction.trans_type):
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete transaction #{transaction.id} ({transaction.category} - ₱{transaction.amount:,.2f})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.service.delete_transaction(self.editing_id)
            self.clear_form()
            self.refresh()
            if self.refresh_callback:
                self.refresh_callback()

    def clear_form(self):
        self.table.clearSelection()
        self.editing_id = None
        self.category_input.clear()
        self.amount_input.clear()
        self.desc_input.clear()
        self.date_input.setDate(QDate.currentDate())
        self.btn_save.setText("Save")

    def refresh(self):
        self.all_transactions = self.service.get_all_transactions()
        self.apply_filters()

    def apply_filters(self):
        search_term = self.search_input.text().lower().strip()
        period_val = self.period_filter.currentText()
        today = QDate.currentDate()

        filtered = []
        for t in self.all_transactions:
            if period_val != "All Time" and t.date:
                t_qdate = QDate.fromString(t.date, "yyyy-MM-dd")
                if t_qdate.isValid():
                    if period_val == "This Month" and (t_qdate.month() != today.month() or t_qdate.year() != today.year()):
                        continue
                    elif period_val == "Last Month":
                        last_m = today.addMonths(-1)
                        if t_qdate.month() != last_m.month() or t_qdate.year() != last_m.year():
                            continue
                    elif period_val == "This Year" and t_qdate.year() != today.year():
                        continue

            if search_term and (
                search_term not in t.category.lower()
                and search_term not in t.description.lower()
            ):
                continue

            filtered.append(t)

        self.table.setRowCount(len(filtered))
        for row, t in enumerate(filtered):
            items = [
                str(t.id),
                str(t.date),
                t.trans_type,
                t.category,
                f"₱{t.amount:,.2f}",
                t.description,
            ]
            for col, val in enumerate(items):
                self.table.setItem(row, col, QTableWidgetItem(val))