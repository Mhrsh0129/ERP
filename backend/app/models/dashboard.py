"""
models/dashboard.py — DB queries for the main dashboard stats page.
"""

from app.core.database import get_db_connection
from datetime import date


class Dashboard:
    @staticmethod
    def get_stats():
        """
        Returns summary stats: total counts, total amounts, recent transactions.
        Runs several simple SELECT queries and bundles the results into one dict.
        """
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) AS total FROM incoming_stock")
        total_incoming = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM outgoing_stock")
        total_outgoing = cur.fetchone()["total"]

        cur.execute("SELECT SUM(amount) AS total FROM incoming_stock")
        total_purchase = cur.fetchone()["total"] or 0

        cur.execute("SELECT SUM(total_amount) AS total FROM outgoing_stock")
        total_sales = cur.fetchone()["total"] or 0

        cur.execute("SELECT SUM(discount_amount) AS total FROM incoming_stock")
        total_discount_received = cur.fetchone()["total"] or 0

        cur.execute("SELECT SUM(discount_amount) AS total FROM outgoing_stock")
        total_discount_given = cur.fetchone()["total"] or 0

        cur.execute("""
            SELECT product_name, source_name, date_of_purchase, quantity, unit, price_per_unit, amount
            FROM incoming_stock ORDER BY date_of_purchase DESC LIMIT 5
        """)
        recent_incoming = cur.fetchall()
        for row in recent_incoming:
            if isinstance(row.get("date_of_purchase"), date):
                row["date_of_purchase"] = row["date_of_purchase"].isoformat()

        cur.execute("""
            SELECT product_name, customer_name, date_of_sale, total_amount
            FROM outgoing_stock ORDER BY date_of_sale DESC LIMIT 5
        """)
        recent_outgoing = cur.fetchall()
        for row in recent_outgoing:
            if isinstance(row.get("date_of_sale"), date):
                row["date_of_sale"] = row["date_of_sale"].isoformat()
            # Alias total_amount to "amount" for frontend compatibility
            if "total_amount" in row:
                row["amount"] = row["total_amount"]

        cur.close()
        conn.close()

        return {
            "total_incoming": total_incoming,
            "total_outgoing": total_outgoing,
            "total_purchase_amount": float(total_purchase),
            "total_sales_amount": float(total_sales),
            "total_discount_received": float(total_discount_received),
            "total_discount_given": float(total_discount_given),
            "low_stock_count": 0,
            "recent_incoming": recent_incoming,
            "recent_outgoing": recent_outgoing,
        }
