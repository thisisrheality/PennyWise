import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List


class DashboardService:

    def __init__(self, db):
        self.db = db

    def _resolve_period_key(self, period_key: str) -> str:
        """Converts human-readable UI dropdown strings ('This Month', 'Last Month', 'All Time')
        into standard 'YYYY-MM' database strings or 'ALL'.
        """
        if not period_key:
            return datetime.now().strftime("%Y-%m")

        clean_key = str(period_key).strip().upper()
        now = datetime.now()

        if clean_key in ("ALL", "ALL TIME", "ALL-TIME"):
            return "ALL"
        elif clean_key in ("THIS MONTH", "CURRENT MONTH"):
            return now.strftime("%Y-%m")
        elif clean_key in ("LAST MONTH", "PREVIOUS MONTH"):
            first_day_this_month = now.replace(day=1)
            last_day_prev_month = first_day_this_month - timedelta(days=1)
            return last_day_prev_month.strftime("%Y-%m")

        return period_key

    def ensure_monthly_rollover(self, current_month: str) -> float:
        """Checks if a 'Rollover' entry exists for `current_month` (e.g. '2026-10').
        If not, calculates the net liquid balance from the previous month and inserts a 'Rollover' transaction.
        """
        if current_month == "ALL":
            return 0.0

        conn = self.db.connect()
        cursor = conn.cursor()

        # 1. Check if Rollover transaction already logged for this month
        cursor.execute(
            """
            SELECT amount FROM transactions 
            WHERE strftime('%Y-%m', date) = ? AND LOWER(TRIM(type)) = 'rollover'
            """,
            (current_month,),
        )
        row = cursor.fetchone()
        if row is not None:
            conn.close()
            return float(row[0])

        # 2. Determine previous month string (e.g. '2026-09')
        year, month = map(int, current_month.split("-"))
        if month == 1:
            prev_month = f"{year - 1}-12"
        else:
            prev_month = f"{year}-{month - 1:02d}"

        # 3. Calculate remaining unallocated liquid cash from previous month
        cursor.execute(
            """
            SELECT 
                COALESCE(SUM(CASE WHEN LOWER(TRIM(type)) IN ('income', 'rollover') THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN LOWER(TRIM(type)) = 'expense' THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN LOWER(TRIM(type)) IN ('savings', 'savings deposit', 'savings_deposit', 'deposit') THEN amount ELSE 0 END), 0) +
                COALESCE(SUM(CASE WHEN LOWER(TRIM(type)) IN ('savings withdrawal', 'savings_withdrawal', 'savings refund', 'withdrawal') THEN amount ELSE 0 END), 0)
            FROM transactions
            WHERE strftime('%Y-%m', date) = ?
            """,
            (prev_month,),
        )
        prev_liquid_remaining = float(cursor.fetchone()[0])

        # 4. If positive remaining balance exists, log as Rollover transaction
        if prev_liquid_remaining > 0:
            rollover_date = f"{current_month}-01"
            cursor.execute(
                """
                INSERT INTO transactions (date, type, category, amount, description)
                VALUES (?, 'Rollover', 'Carryover', ?, 'Unspent liquid cash from prior month')
                """,
                (rollover_date, prev_liquid_remaining),
            )
            conn.commit()

        conn.close()
        return prev_liquid_remaining

    def get_summary(self, period_key: str = "This Month") -> Dict[str, Any]:
        """Calculates liquid rollover balance, period cash flows, cumulative savings, and individual goal progress."""
        resolved_key = self._resolve_period_key(period_key)

        # Auto-ensure rollover entry exists for selected month
        if resolved_key != "ALL":
            self.ensure_monthly_rollover(resolved_key)

        conn = self.db.connect()
        cursor = conn.cursor()

        savings_dep_clause = """
            (
                LOWER(TRIM(type)) IN ('savings', 'savings deposit', 'savings_deposit', 'deposit')
                OR (LOWER(TRIM(type)) LIKE '%savings%' AND LOWER(TRIM(type)) NOT LIKE '%withdraw%' AND LOWER(TRIM(type)) NOT LIKE '%refund%')
            )
        """
        savings_ret_clause = """
            (
                LOWER(TRIM(type)) IN ('savings withdrawal', 'savings_withdrawal', 'savings refund', 'withdrawal')
                OR LOWER(TRIM(type)) LIKE '%withdraw%' OR LOWER(TRIM(type)) LIKE '%refund%'
            )
        """

        if resolved_key == "ALL":
            trans_where = ""
            params = []

            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0.0) FROM transactions WHERE LOWER(TRIM(type)) = 'income'"
            )
            period_income = float(cursor.fetchone()[0])

            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0.0) FROM transactions WHERE LOWER(TRIM(type)) = 'expense'"
            )
            period_expenses = float(cursor.fetchone()[0])

            cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0.0) FROM transactions WHERE {savings_dep_clause}"
            )
            period_savings_dep = float(cursor.fetchone()[0])

            cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0.0) FROM transactions WHERE {savings_ret_clause}"
            )
            period_savings_returns = float(cursor.fetchone()[0])

            starting_balance = 0.0
            period_savings_net = period_savings_dep - period_savings_returns
            period_net = period_income - period_expenses
            liquid_balance = period_net - period_savings_net

            cursor.execute("SELECT COALESCE(SUM(current_amount), 0.0) FROM savings_goals")
            goal_vault_total = float(cursor.fetchone()[0])
            total_savings = max(period_savings_net, goal_vault_total)

        else:
            trans_where = "WHERE strftime('%Y-%m', date) = ?"
            params = [resolved_key]

            # 1. Fetch Rollover Amount for the selected period
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0.0) FROM transactions 
                WHERE strftime('%Y-%m', date) = ? AND LOWER(TRIM(type)) = 'rollover'
                """,
                (resolved_key,),
            )
            starting_balance = float(cursor.fetchone()[0])

            # 2. Real Income Earned in this period
            cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0.0) FROM transactions {trans_where} AND LOWER(TRIM(type)) = 'income'",
                params,
            )
            period_income = float(cursor.fetchone()[0])

            # 3. Expenses Spent in this period
            cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0.0) FROM transactions {trans_where} AND LOWER(TRIM(type)) = 'expense'",
                params,
            )
            period_expenses = float(cursor.fetchone()[0])

            # 4. Savings Deposited / Withdrawn in this period
            cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0.0) FROM transactions {trans_where} AND {savings_dep_clause}",
                params,
            )
            period_savings_dep = float(cursor.fetchone()[0])

            cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0.0) FROM transactions {trans_where} AND {savings_ret_clause}",
                params,
            )
            period_savings_returns = float(cursor.fetchone()[0])

            period_savings_net = period_savings_dep - period_savings_returns
            period_net = period_income - period_expenses

            # Unallocated Liquid Balance = Rollover + Income - Expenses - Savings Deposited
            liquid_balance = starting_balance + period_net - period_savings_net

            # 5. Savings Vault Assets total up to end of selected period
            cursor.execute(
                f"""
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN {savings_dep_clause} THEN amount 
                        WHEN {savings_ret_clause} THEN -amount 
                        ELSE 0 
                    END
                ), 0.0) 
                FROM transactions 
                WHERE strftime('%Y-%m', date) <= ?
                """,
                (resolved_key,),
            )
            tx_savings_total = float(cursor.fetchone()[0])

            cursor.execute("SELECT COALESCE(SUM(current_amount), 0.0) FROM savings_goals")
            goal_vault_total = float(cursor.fetchone()[0])

            total_savings = max(tx_savings_total, goal_vault_total)

        # 6. Fetch individual savings goals with calculated progress percentages
        cursor.execute("SELECT id, title, target_amount, current_amount FROM savings_goals ORDER BY id ASC")
        savings_goals_data = []
        for row in cursor.fetchall():
            g_id, title, target, current = row[0], row[1], float(row[2]), float(row[3])
            pct = (current / target * 100.0) if target > 0 else 0.0
            savings_goals_data.append(
                {
                    "id": g_id,
                    "title": title,
                    "target_amount": target,
                    "current_amount": current,
                    "progress_pct": min(100.0, round(pct, 1)),
                }
            )

        # 7. Expense Breakdown
        where_exp_cat = (
            f"{trans_where} AND LOWER(TRIM(type)) = 'expense'"
            if trans_where
            else "WHERE LOWER(TRIM(type)) = 'expense'"
        )
        cursor.execute(
            f"""
            SELECT category, SUM(amount) as cat_total 
            FROM transactions 
            {where_exp_cat} 
            GROUP BY category 
            ORDER BY cat_total DESC
            """,
            params,
        )
        expense_breakdown = {row[0]: float(row[1]) for row in cursor.fetchall()}

        # 8. Budgets
        if resolved_key == "ALL":
            cursor.execute(
                "SELECT id, category, monthly_limit FROM budgets GROUP BY category ORDER BY category ASC"
            )
        else:
            cursor.execute(
                "SELECT id, category, monthly_limit FROM budgets WHERE month = ? ORDER BY category ASC",
                (resolved_key,),
            )

        budget_rows = cursor.fetchall()
        if not budget_rows and resolved_key != "ALL":
            cursor.execute(
                "SELECT id, category, monthly_limit FROM budgets GROUP BY category ORDER BY category ASC"
            )
            budget_rows = cursor.fetchall()

        budgets_data = []
        for b_id, cat, limit in budget_rows:
            if resolved_key == "ALL":
                cursor.execute(
                    "SELECT COALESCE(SUM(amount), 0.0) FROM transactions WHERE LOWER(TRIM(type)) = 'expense' AND LOWER(category) = LOWER(?)",
                    (cat,),
                )
            else:
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0.0) 
                    FROM transactions 
                    WHERE strftime('%Y-%m', date) = ? AND LOWER(TRIM(type)) = 'expense' AND LOWER(category) = LOWER(?)
                    """,
                    (resolved_key, cat),
                )

            spent = float(cursor.fetchone()[0])
            budgets_data.append(
                {
                    "id": b_id,
                    "category": cat,
                    "monthly_limit": float(limit),
                    "spent": spent,
                }
            )

        # 9. Recent Transactions
        cursor.execute(
            f"""
            SELECT date, type, category, amount, description 
            FROM transactions 
            {trans_where} 
            ORDER BY date DESC, id DESC 
            LIMIT 5
            """,
            params,
        )
        recent_txs = [
            {
                "date": r[0],
                "type": r[1],
                "category": r[2],
                "amount": float(r[3]),
                "description": r[4],
            }
            for r in cursor.fetchall()
        ]

        conn.close()

        return {
            "starting_balance": starting_balance,
            "income": period_income,
            "expenses": period_expenses,
            "period_net": period_net,
            "savings_allocated": period_savings_net,
            "balance": liquid_balance,
            # Dict key aliases so dashboard view.py binds correctly
            "total_savings": total_savings,
            "savings_vault": total_savings,
            "savings_total": total_savings,
            "savings": total_savings,
            "savings_goals": savings_goals_data,
            "total_net_worth": liquid_balance + total_savings,
            "expense_breakdown": expense_breakdown,
            "budgets": budgets_data,
            "recent_transactions": recent_txs,
        }