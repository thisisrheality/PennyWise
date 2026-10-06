import random
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

PENNYWISE_HORROR_QUOTES = [
    "\"We all float down here... and when you're down here with me, YOU'LL FLOAT TOO! 🎈\"",
    "\"Take a balloon... they float. Everything floats down in the sewer.\" 🎈",
    "\"Pennywise counts every drop of blood... and every single penny.\" 🎈",
    "\"Is your budget leaking? Or is it bleeding out in the dark?\" 🎈",
    "\"For 27 years I slept... until your debt woke me up!\" 🎈",
]


class DashboardView(QWidget):

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("dashboardView")
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll container to prevent UI clipping on smaller windows
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("dashboardScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container.setObjectName("dashboardContainer")

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Header Bar
        hdr = QFrame()
        hdr.setObjectName("viewHeaderBar")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(16, 10, 16, 10)

        lbl_title = QLabel("FINANCIAL DASHBOARD 🎈")
        lbl_title.setObjectName("viewHeaderTitle")

        filter_box = QHBoxLayout()
        filter_box.setSpacing(8)
        lbl_f = QLabel("Period:")
        lbl_f.setObjectName("headerLabel")

        self.period_mode = QComboBox()
        self.period_mode.setObjectName("periodDropdown")
        self.period_mode.addItems(["This Month", "All Time", "Select Specific Month"])
        self.period_mode.currentTextChanged.connect(self.on_period_changed)

        self.month_picker = QDateEdit()
        self.month_picker.setObjectName("monthPicker")
        self.month_picker.setDisplayFormat("yyyy-MM")
        self.month_picker.setDate(QDate.currentDate())
        self.month_picker.setCalendarPopup(True)
        self.month_picker.setVisible(False)
        self.month_picker.dateChanged.connect(lambda: self.refresh())

        filter_box.addWidget(lbl_f)
        filter_box.addWidget(self.period_mode)
        filter_box.addWidget(self.month_picker)

        hdr_l.addWidget(lbl_title)
        hdr_l.addStretch()
        hdr_l.addLayout(filter_box)
        main_layout.addWidget(hdr, stretch=0)

        # 2. KPI Ribbon (3 metrics — Savings card removed to omit redundancy)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)
        self.lbl_bal = self._add_kpi(kpi_row, "NET BALANCE", "kpiValBalance", "Surviving Cash")
        self.lbl_inc = self._add_kpi(kpi_row, "TOTAL INFLOW", "kpiValIncome", "Income & Cash-In")
        self.lbl_exp = self._add_kpi(kpi_row, "TOTAL OUTFLOW", "kpiValExpense", "Expenses & Losses")
        main_layout.addLayout(kpi_row)

        # 3. Main Split Body
        body = QHBoxLayout()
        body.setSpacing(12)

        # Left Column: Recent Activity, Insights, & Savings Goals
        left_card = QFrame()
        left_card.setObjectName("cardFrame")
        l_layout = QVBoxLayout(left_card)
        l_layout.setContentsMargins(14, 14, 14, 14)
        l_layout.setSpacing(10)

        # Recent Transactions
        lbl_t = QLabel("RECENT TRANSACTIONS")
        lbl_t.setObjectName("sectionHeader")
        l_layout.addWidget(lbl_t)

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("transactionTable")
        self.table.setHorizontalHeaderLabels(["DATE", "TYPE", "CATEGORY", "AMOUNT"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        l_layout.addWidget(self.table, stretch=1)

        # Insight Summary Box
        left_insight = QFrame()
        left_insight.setObjectName("innerInsightCard")
        li_layout = QHBoxLayout(left_insight)
        li_layout.setContentsMargins(10, 8, 10, 8)

        self.lbl_left_insight_text = QLabel("💡 <b>Vault Status:</b> Activity logged cleanly for current cycle.")
        self.lbl_left_insight_text.setObjectName("subText")
        li_layout.addWidget(self.lbl_left_insight_text)
        l_layout.addWidget(left_insight)

        div_left = QFrame()
        div_left.setObjectName("sectionDivider")
        l_layout.addWidget(div_left)

        # Savings Goals Progress Section (Moved to Left Side)
        lbl_sg_header = QLabel("SAVINGS GOALS PROGRESS 🎈")
        lbl_sg_header.setObjectName("sectionHeader")
        l_layout.addWidget(lbl_sg_header)

        self.savings_container = QVBoxLayout()
        self.savings_container.setSpacing(6)
        l_layout.addLayout(self.savings_container)

        body.addWidget(left_card, stretch=55)

        # Right Column: Expense Breakdown, Budgeting, Vault Velocity
        right_card = QFrame()
        right_card.setObjectName("cardFrame")
        r_layout = QVBoxLayout(right_card)
        r_layout.setContentsMargins(14, 14, 14, 14)
        r_layout.setSpacing(10)

        # Expense Breakdown Section
        lbl_exp_header = QLabel("EXPENSE BREAKDOWN")
        lbl_exp_header.setObjectName("sectionHeader")
        lbl_exp_desc = QLabel("Categorized distribution for selected period.")
        lbl_exp_desc.setObjectName("subText")

        r_layout.addWidget(lbl_exp_header)
        r_layout.addWidget(lbl_exp_desc)

        self.cat_container = QVBoxLayout()
        self.cat_container.setSpacing(6)
        r_layout.addLayout(self.cat_container)

        div1 = QFrame()
        div1.setObjectName("sectionDivider")
        r_layout.addWidget(div1)

        # Budget Tracking Section
        lbl_b_header = QLabel("BUDGET TRACKING")
        lbl_b_header.setObjectName("sectionHeader")
        r_layout.addWidget(lbl_b_header)

        self.budget_container = QVBoxLayout()
        self.budget_container.setSpacing(6)
        r_layout.addLayout(self.budget_container)

        div2 = QFrame()
        div2.setObjectName("sectionDivider")
        r_layout.addWidget(div2)

        # Vault Health Meter Widget
        right_insight = QFrame()
        right_insight.setObjectName("innerInsightCard")
        ri_layout = QVBoxLayout(right_insight)
        ri_layout.setContentsMargins(10, 8, 10, 8)
        ri_layout.setSpacing(4)

        lbl_meter_title = QLabel("VAULT HEALTH & SPENDING VELOCITY")
        lbl_meter_title.setObjectName("kpiHeader")
        self.lbl_meter_status = QLabel("● Stable Consumption")
        self.lbl_meter_status.setObjectName("healthMeterStatus")

        self.velocity_bar = QProgressBar()
        self.velocity_bar.setObjectName("pbarNormal")
        self.velocity_bar.setFixedHeight(8)
        self.velocity_bar.setTextVisible(False)
        self.velocity_bar.setValue(45)

        ri_layout.addWidget(lbl_meter_title)
        ri_layout.addWidget(self.lbl_meter_status)
        ri_layout.addWidget(self.velocity_bar)
        r_layout.addWidget(right_insight)

        body.addWidget(right_card, stretch=45)
        main_layout.addLayout(body, stretch=1)

        # 4. Pennywise Footer Quote Banner
        quote_card = QFrame()
        quote_card.setObjectName("quoteCard")
        q_layout = QHBoxLayout(quote_card)
        q_layout.setContentsMargins(14, 8, 14, 8)

        self.lbl_quote = QLabel(random.choice(PENNYWISE_HORROR_QUOTES))
        self.lbl_quote.setObjectName("quoteText")
        q_layout.addWidget(self.lbl_quote)
        main_layout.addWidget(quote_card, stretch=0)

        scroll_area.setWidget(container)
        root_layout.addWidget(scroll_area)

    def _add_kpi(self, layout, title: str, val_id: str, desc: str) -> QLabel:
        tile = QFrame()
        tile.setObjectName("kpiTile")
        tl = QVBoxLayout(tile)
        tl.setContentsMargins(12, 10, 12, 10)
        tl.setSpacing(2)

        t = QLabel(title)
        t.setObjectName("kpiHeader")
        v = QLabel("₱0.00")
        v.setObjectName(val_id)
        d = QLabel(desc)
        d.setObjectName("kpiDesc")

        tl.addWidget(t)
        tl.addWidget(v)
        tl.addWidget(d)
        layout.addWidget(tile)
        return v

    def _set_bar_style(self, bar: QProgressBar, style_name: str):
        """Forces Qt to re-polish QSS rules when changing progress bar object names dynamically."""
        if bar.objectName() != style_name:
            bar.setObjectName(style_name)
            bar.style().unpolish(bar)
            bar.style().polish(bar)

    def on_period_changed(self, mode: str):
        self.month_picker.setVisible(mode == "Select Specific Month")
        self.refresh()

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

    def refresh(self):
        mode = self.period_mode.currentText()
        if mode == "This Month":
            period_key = QDate.currentDate().toString("yyyy-MM")
        elif mode == "Select Specific Month":
            period_key = self.month_picker.date().toString("yyyy-MM")
        else:
            period_key = "ALL"

        data = self.service.get_summary(period_key)

        inc = float(data.get("income", 0))
        exp = float(data.get("expenses", 0))
        bal = float(data.get("balance", 0))

        self.lbl_bal.setText(f"₱{bal:,.2f}")
        self.lbl_inc.setText(f"₱{inc:,.2f}")
        self.lbl_exp.setText(f"₱{exp:,.2f}")

        # Spending Velocity / Burn Ratio calculation
        burn_ratio = min(100, int((exp / inc) * 100)) if inc > 0 else (100 if exp > 0 else 0)
        self.velocity_bar.setValue(burn_ratio)

        if burn_ratio > 85:
            self.lbl_meter_status.setText("⚠️ HIGH DRAIN DETECTED")
            self.lbl_meter_status.setStyleSheet("color: #FF2E2E; font-weight: 700; font-size: 11px;")
            self._set_bar_style(self.velocity_bar, "pbarDanger")
        elif burn_ratio > 50:
            self.lbl_meter_status.setText("⚡ MODERATE SPENDING VELOCITY")
            self.lbl_meter_status.setStyleSheet("color: #F59E0B; font-weight: 700; font-size: 11px;")
            self._set_bar_style(self.velocity_bar, "pbarWarning")
        else:
            self.lbl_meter_status.setText("● STABLE CONSUMPTION")
            self.lbl_meter_status.setStyleSheet("color: #22C55E; font-weight: 700; font-size: 11px;")
            self._set_bar_style(self.velocity_bar, "pbarNormal")

        # Top Recent Transactions Table
        recent = data.get("recent_transactions", [])[:5]
        self.table.setRowCount(len(recent))
        for row, t in enumerate(recent):
            if isinstance(t, dict):
                t_date = t.get("date", "")
                t_type = t.get("type", t.get("trans_type", ""))
                t_cat = t.get("category", "")
                t_amt = float(t.get("amount", 0.0))
            else:
                t_date = getattr(t, "date", "")
                t_type = getattr(t, "type", getattr(t, "trans_type", ""))
                t_cat = getattr(t, "category", "")
                t_amt = float(getattr(t, "amount", 0.0))

            self.table.setItem(row, 0, QTableWidgetItem(str(t_date)))
            self.table.setItem(row, 1, QTableWidgetItem(str(t_type)))
            self.table.setItem(row, 2, QTableWidgetItem(str(t_cat)))
            self.table.setItem(row, 3, QTableWidgetItem(f"₱{t_amt:,.2f}"))

        self.lbl_left_insight_text.setText(
            f"💡 <b>Vault Summary:</b> {len(recent)} recent entries logged for {period_key}."
        )

        # Savings Goals Progress Section (Left Column)
        self._clear_layout(self.savings_container)
        savings_goals = data.get("savings_goals", [])
        if not savings_goals:
            empty_sg = QLabel("No active savings goals set.")
            empty_sg.setObjectName("emptyStateLabel")
            self.savings_container.addWidget(empty_sg)
        else:
            for goal in savings_goals[:4]:
                title = goal.get("title", "Goal")
                cur = float(goal.get("current_amount", 0.0))
                tgt = float(goal.get("target_amount", 0.0))
                pct = int(goal.get("progress_pct", 0))

                sg_row = QHBoxLayout()
                lbl_title = QLabel(title)
                lbl_title.setObjectName("goalTitle")
                lbl_vals = QLabel(f"₱{cur:,.2f} / ₱{tgt:,.2f} ({pct}%)")
                lbl_vals.setObjectName("goalAmount")

                sg_row.addWidget(lbl_title)
                sg_row.addStretch()
                sg_row.addWidget(lbl_vals)

                sbar = QProgressBar()
                sbar.setValue(min(100, pct))
                sbar.setFixedHeight(6)
                sbar.setTextVisible(False)
                self._set_bar_style(sbar, "pbarSavings")

                self.savings_container.addLayout(sg_row)
                self.savings_container.addWidget(sbar)

        # Expense Breakdown Section (Right Column)
        self._clear_layout(self.cat_container)
        expense_breakdown = data.get("expense_breakdown", {})
        if not expense_breakdown:
            empty_lbl = QLabel("No expense activity logged for this period.")
            empty_lbl.setObjectName("emptyStateLabel")
            self.cat_container.addWidget(empty_lbl)
        else:
            total_exp = sum(expense_breakdown.values()) or 1.0
            for cat, amt in list(expense_breakdown.items())[:4]:
                row_box = QHBoxLayout()
                lbl_c = QLabel(cat)
                lbl_c.setObjectName("breakdownCategory")
                lbl_a = QLabel(f"₱{amt:,.2f}")
                lbl_a.setObjectName("breakdownAmount")

                row_box.addWidget(lbl_c)
                row_box.addStretch()
                row_box.addWidget(lbl_a)

                pbar = QProgressBar()
                pbar.setValue(int((amt / total_exp) * 100))
                pbar.setFixedHeight(6)
                pbar.setTextVisible(False)
                self._set_bar_style(pbar, "pbarNormal")

                self.cat_container.addLayout(row_box)
                self.cat_container.addWidget(pbar)

        # Budget Tracking Section (Right Column)
        self._clear_layout(self.budget_container)
        budgets = data.get("budgets", [])
        if not budgets:
            empty_b = QLabel("No active budget limits configured.")
            empty_b.setObjectName("emptyStateLabel")
            self.budget_container.addWidget(empty_b)
        else:
            for b in budgets[:3]:
                if isinstance(b, dict):
                    cat = b.get("category", "Uncategorized")
                    spent = float(b.get("spent", 0.0))
                    limit = float(b.get("monthly_limit", b.get("limit", 0.0)))
                else:
                    cat = getattr(b, "category", "Uncategorized")
                    spent = float(getattr(b, "spent", 0.0))
                    limit = float(getattr(b, "monthly_limit", getattr(b, "limit", 0.0)))

                b_row = QHBoxLayout()
                lbl_name = QLabel(cat)
                lbl_name.setObjectName("budgetCategory")
                lbl_stat = QLabel(f"₱{spent:,.2f} / ₱{limit:,.2f}")
                lbl_stat.setObjectName("budgetAmount")

                b_row.addWidget(lbl_name)
                b_row.addStretch()
                b_row.addWidget(lbl_stat)

                pct = int((spent / limit) * 100) if limit > 0 else 0
                bbar = QProgressBar()
                bbar.setValue(min(100, pct))
                bbar.setFixedHeight(6)
                bbar.setTextVisible(False)

                if pct > 100:
                    self._set_bar_style(bbar, "pbarDanger")
                elif pct > 85:
                    self._set_bar_style(bbar, "pbarWarning")
                else:
                    self._set_bar_style(bbar, "pbarNormal")

                self.budget_container.addLayout(b_row)
                self.budget_container.addWidget(bbar)