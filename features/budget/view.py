from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .model import Budget


class BudgetView(QWidget):

    def __init__(self, service, refresh_callback=None):
        super().__init__()
        self.service = service
        self.refresh_callback = refresh_callback
        self.editing_id = None
        self.current_budgets = []
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

        lbl_title = QLabel("MONTHLY BUDGETS")
        lbl_title.setObjectName("viewHeaderTitle")

        filter_box = QHBoxLayout()
        filter_box.setSpacing(8)
        month_label = QLabel("Period:")
        month_label.setObjectName("headerLabel")

        self.month_picker = QDateEdit()
        self.month_picker.setDisplayFormat("yyyy-MM")
        self.month_picker.setDate(QDate.currentDate())
        self.month_picker.setCalendarPopup(True)
        self.month_picker.setFixedWidth(110)
        self.month_picker.dateChanged.connect(lambda: self.refresh())

        filter_box.addWidget(month_label)
        filter_box.addWidget(self.month_picker)

        hdr_l.addWidget(lbl_title)
        hdr_l.addStretch()
        hdr_l.addLayout(filter_box)
        layout.addWidget(hdr, stretch=0)

        # Card Frame
        card = QFrame()
        card.setObjectName("cardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(12)

        # Form Bar
        form_bar = QHBoxLayout()
        form_bar.setSpacing(8)

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Category (e.g. Groceries)")

        self.limit_input = QLineEdit()
        self.limit_input.setPlaceholderText("Monthly Limit (₱)")
        self.limit_input.setFixedWidth(140)

        self.btn_save = QPushButton("Save Budget")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.clicked.connect(lambda: self.save_budget())

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.clicked.connect(lambda: self.delete_budget())

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setObjectName("secondaryButton")
        self.btn_clear.clicked.connect(lambda: self.clear_form())

        form_bar.addWidget(self.category_input, stretch=2)
        form_bar.addWidget(self.limit_input)
        form_bar.addWidget(self.btn_save)
        form_bar.addWidget(self.btn_delete)
        form_bar.addWidget(self.btn_clear)

        c_layout.addLayout(form_bar)

        # Empty State Label
        self.empty_state_lbl = QLabel("No budget limits set for this period. Add one above to start tracking!")
        self.empty_state_lbl.setObjectName("emptyStateLabel")
        self.empty_state_lbl.setVisible(False)
        c_layout.addWidget(self.empty_state_lbl)

        # Table Widget
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "CATEGORY",
                "MONTHLY BUDGET",
                "SPENT THIS MONTH",
                "REMAINING",
                "USAGE PROGRESS",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_row_selected)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        c_layout.addWidget(self.table)
        layout.addWidget(card, stretch=1)

    def save_budget(self):
        try:
            cat = self.category_input.text().strip()
            if not cat:
                raise ValueError("Please enter a category name.")

            try:
                limit = float(self.limit_input.text() or 0)
            except ValueError:
                raise ValueError("Limit must be a valid number.")

            if limit <= 0:
                raise ValueError("Budget limit must be greater than zero.")

            selected_month = self.month_picker.date().toString("yyyy-MM")

            b = Budget(
                category=cat,
                monthly_limit=limit,
                month=selected_month,
                id=self.editing_id,
            )

            self.service.set_budget(b)
            self.clear_form()
            self.refresh()

            if self.refresh_callback:
                self.refresh_callback()

        except Exception as err:
            QMessageBox.warning(self, "Budget Error", str(err))

    def on_row_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return

        row = self.table.currentRow()
        b_id = int(self.table.item(row, 0).text())
        item = next((b for b in self.current_budgets if b["id"] == b_id), None)

        if not item:
            return

        self.editing_id = item["id"]
        self.category_input.setText(item["category"])
        self.limit_input.setText(str(item["monthly_limit"]))
        self.btn_save.setText("Update Budget")

    def delete_budget(self):
        row = self.table.currentRow()
        if row < 0 or self.editing_id is None:
            QMessageBox.warning(
                self, "Select Item", "Please select a budget row to delete."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this budget limit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.delete_budget(self.editing_id)
                self.clear_form()
                self.refresh()
                if self.refresh_callback:
                    self.refresh_callback()
            except Exception as err:
                QMessageBox.warning(self, "Delete Error", str(err))

    def clear_form(self):
        self.table.clearSelection()
        self.editing_id = None
        self.category_input.clear()
        self.limit_input.clear()
        self.btn_save.setText("Save Budget")

    def refresh(self):
        selected_month = self.month_picker.date().toString("yyyy-MM")
        self.current_budgets = self.service.get_budgets_for_month(selected_month)

        if not self.current_budgets:
            self.table.setVisible(False)
            self.empty_state_lbl.setVisible(True)
            self.table.setRowCount(0)
            return

        self.table.setVisible(True)
        self.empty_state_lbl.setVisible(False)
        self.table.setRowCount(len(self.current_budgets))

        for row, b in enumerate(self.current_budgets):
            limit = b["monthly_limit"]
            spent = b["spent"]
            remaining = b["remaining"]

            pct = int((spent / limit) * 100) if limit > 0 else 0
            pct_clamped = min(100, pct)

            self.table.setItem(row, 0, QTableWidgetItem(str(b["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(b["category"]))
            self.table.setItem(row, 2, QTableWidgetItem(f"₱{limit:,.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"₱{spent:,.2f}"))

            rem_item = QTableWidgetItem(f"₱{remaining:,.2f}")
            if remaining < 0:
                rem_item.setText(f"₱{remaining:,.2f} (Over)")
            self.table.setItem(row, 4, rem_item)

            bar = QProgressBar()
            bar.setValue(pct_clamped)
            if pct > 100:
                bar.setObjectName("pbarDanger")
            elif pct > 85:
                bar.setObjectName("pbarWarning")
            else:
                bar.setObjectName("pbarNormal")

            self.table.setCellWidget(row, 5, bar)