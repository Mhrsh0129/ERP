"""
models/inventory.py — DB operations for the live_inventory view and product_details table.

live_inventory is a SQL VIEW — not a real table.
It automatically calculates current stock = purchased - sold for each product.
"""

from app.core.database import get_db_connection
import base64


class LiveInventory:
    @staticmethod
    def get_all():
        """
        Returns current stock level for every product, with supplier info and photo.
        Reads from the live_inventory VIEW joined with product_details.
        """
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT
                li.product_name,
                li.current_stock,
                li.unit,
                pd.details,
                (SELECT product_photo FROM incoming_stock
                 WHERE product_name = li.product_name
                   AND product_photo IS NOT NULL
                 ORDER BY date_of_purchase DESC LIMIT 1) AS product_photo,
                (SELECT GROUP_CONCAT(DISTINCT source_name ORDER BY source_name SEPARATOR ', ')
                 FROM incoming_stock
                 WHERE product_name = li.product_name
                   AND source_name IS NOT NULL) AS source_name
            FROM live_inventory li
            LEFT JOIN product_details pd ON li.product_name = pd.product_name
            ORDER BY li.product_name
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for row in rows:
            if row.get("product_photo"):
                row["product_photo"] = base64.b64encode(row["product_photo"]).decode(
                    "utf-8"
                )
        return rows

    @staticmethod
    def get_low_stock():
        """Returns products running low. Currently empty — no reorder level in DB yet."""
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.close()
        conn.close()
        return []

    @staticmethod
    def update_details(product_name, details):
        """
        Saves extra notes for a product.
        INSERT ... ON DUPLICATE KEY UPDATE = "upsert": insert if new, update if exists.
        """
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO product_details (product_name, details)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE details = VALUES(details)
        """,
            (product_name, details),
        )
        conn.commit()
        cur.close()
        conn.close()
