"""
models/incoming_stock.py — DB operations for the incoming_stock table.

A "model" groups all database functions for one table.
Each function does one specific DB task and returns plain data — no wrapping.

Why @staticmethod?
  These functions don't need any instance data (no "self").
  It's just a clean way to group related functions under one name.
"""

from app.core.database import get_db_connection
from datetime import date, datetime
import base64


# ── Helpers ───────────────────────────────────────────────────────────────────


def encode_photos(row, fields=("product_photo", "bill_photo", "bilti_photo")):
    """
    MySQL stores photos as raw bytes (BLOB). JSON can't carry raw bytes,
    so we convert them to base64 strings so they can travel as JSON text.
    """
    for f in fields:
        if row.get(f):
            row[f] = base64.b64encode(row[f]).decode("utf-8")


def format_dates(row, keys=("date_of_purchase", "payment_date", "delivery_date")):
    """
    MySQL returns DATE columns as Python date objects.
    JSON can't send date objects, so we convert them to "YYYY-MM-DD" strings.
    """
    for k in keys:
        if row.get(k) and isinstance(row[k], (date, datetime)):
            row[k] = row[k].isoformat()


def decode_photo(val):
    """
    The frontend sends photos as base64 strings, sometimes with a data URI prefix
    like "data:image/png;base64,AAAA...". We strip the prefix and decode to bytes
    for storage in a BLOB column.
    """
    if not val:
        return None
    raw = val.split(",")[1] if "," in val else val
    return base64.b64decode(raw)


# ── IncomingStock ─────────────────────────────────────────────────────────────


class IncomingStock:
    @staticmethod
    def get_all():
        """Returns all rows from incoming_stock, newest first."""
        conn = get_db_connection()
        cur = conn.cursor(
            dictionary=True
        )  # dictionary=True → rows as dicts, not tuples
        cur.execute("""
            SELECT id, product_name, source_name, date_of_purchase,
                   quantity, unit, price_per_unit, tax_percent, discount_amount,
                   tax_amount, amount,
                   payment_status, amount_paid, payment_type, payment_date, delivery_date,
                   product_photo, bill_photo, bilti_photo
            FROM incoming_stock
            ORDER BY date_of_purchase DESC
        """)
        rows = cur.fetchall()  # fetchall() gets every row at once as a list
        cur.close()
        conn.close()  # Returns this connection back to the pool
        for row in rows:
            encode_photos(row)
            format_dates(row)
        return rows

    @staticmethod
    def get_by_id(stock_id):
        """Returns one row by its primary key, or None if not found."""
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, product_name, source_name, date_of_purchase,
                   quantity, unit, price_per_unit, tax_percent, discount_amount,
                   tax_amount, amount,
                   payment_status, amount_paid, payment_type, payment_date, delivery_date,
                   product_photo, bill_photo, bilti_photo
            FROM incoming_stock WHERE id = %s
        """,
            (stock_id,),
        )  # %s is a safe placeholder; (stock_id,) provides the value
        row = cur.fetchone()  # fetchone() gets only the first matching row
        cur.close()
        conn.close()
        if row:
            encode_photos(row)
            format_dates(row)
        return row

    @staticmethod
    def search(query):
        """Returns rows where product_name or source_name contains the search text."""
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        pattern = f"%{query}%"  # % is a wildcard in SQL LIKE — matches anything
        cur.execute(
            """
            SELECT id, product_name, source_name, date_of_purchase,
                   quantity, unit, price_per_unit, tax_percent, tax_amount, amount,
                   payment_status, amount_paid, payment_type, payment_date, delivery_date,
                   product_photo, bill_photo, bilti_photo
            FROM incoming_stock
            WHERE product_name LIKE %s OR source_name LIKE %s
            ORDER BY date_of_purchase DESC
        """,
            (pattern, pattern),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for row in rows:
            encode_photos(row)
            format_dates(row)
        return rows

    @staticmethod
    def create(data):
        """Inserts a new row. Returns the auto-generated id."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO incoming_stock
            (product_name, source_name, date_of_purchase,
             quantity, unit, price_per_unit, tax_percent, discount_amount,
             payment_status, amount_paid, payment_type, payment_date, delivery_date,
             product_photo, bill_photo, bilti_photo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                data["product_name"],
                data.get("source_name"),
                data.get("date_of_purchase"),
                data.get("quantity"),
                data.get("unit"),
                data.get("price_per_unit"),
                data.get("tax_percent"),
                data.get("discount_amount", 0.00),
                data.get("payment_status"),
                data.get("amount_paid"),
                data.get("payment_type"),
                data.get("payment_date"),
                data.get("delivery_date"),
                decode_photo(data.get("product_photo")),
                decode_photo(data.get("bill_photo")),
                decode_photo(data.get("bilti_photo")),
            ),
        )
        conn.commit()  # commit() saves the INSERT to the database permanently
        new_id = cur.lastrowid  # lastrowid gives us the auto-generated primary key
        cur.close()
        conn.close()
        return new_id

    @staticmethod
    def update(stock_id, data):
        """Updates an existing row."""
        conn = get_db_connection()
        cur = conn.cursor()

        # Decode photos only if new images were sent in the request
        photos = {
            f: decode_photo(data[f])
            for f in ["product_photo", "bill_photo", "bilti_photo"]
            if data.get(f)
        }

        base_vals = (
            data["product_name"],
            data.get("source_name"),
            data.get("date_of_purchase"),
            data.get("quantity", 1),
            data.get("unit", "pcs"),
            data.get("price_per_unit", 0),
            data.get("tax_percent", 0),
            data.get("discount_amount", 0.00),
            data.get("payment_status", "pending"),
            data.get("amount_paid", 0),
            data.get("payment_type"),
            data.get("payment_date"),
            data.get("delivery_date"),
        )

        if photos:
            cur.execute(
                """
                UPDATE incoming_stock
                SET product_name=%s, source_name=%s, date_of_purchase=%s,
                    quantity=%s, unit=%s, price_per_unit=%s, tax_percent=%s, discount_amount=%s,
                    payment_status=%s, amount_paid=%s, payment_type=%s, payment_date=%s, delivery_date=%s,
                    product_photo=%s, bill_photo=%s, bilti_photo=%s
                WHERE id=%s
            """,
                (
                    *base_vals,
                    photos.get("product_photo"),
                    photos.get("bill_photo"),
                    photos.get("bilti_photo"),
                    stock_id,
                ),
            )
        else:
            cur.execute(
                """
                UPDATE incoming_stock
                SET product_name=%s, source_name=%s, date_of_purchase=%s,
                    quantity=%s, unit=%s, price_per_unit=%s, tax_percent=%s, discount_amount=%s,
                    payment_status=%s, amount_paid=%s, payment_type=%s, payment_date=%s, delivery_date=%s
                WHERE id=%s
            """,
                (*base_vals, stock_id),
            )

        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def delete(stock_id):
        """Deletes a row by its id."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM incoming_stock WHERE id = %s", (stock_id,))
        conn.commit()
        cur.close()
        conn.close()

    # ── Payments ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_payments(stock_id):
        """Returns all payment instalments for a stock entry."""
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, amount, payment_date, payment_type, notes, created_at
            FROM payment_transactions
            WHERE stock_id = %s ORDER BY payment_date DESC
        """,
            (stock_id,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for row in rows:
            format_dates(row, ["payment_date", "created_at"])
        return rows

    @staticmethod
    def add_payment(stock_id, data):
        """
        Inserts a payment instalment and updates amount_paid + payment_status on the parent row.

        Two SQL statements run here:
          1. INSERT the new payment
          2. UPDATE the parent incoming_stock row to reflect the new total paid
        COALESCE(amount_paid, 0) means "use 0 if amount_paid is NULL"
        CASE...END is SQL's if/elif/else
        """
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO payment_transactions (stock_id, amount, payment_date, payment_type, notes)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (
                stock_id,
                data["amount"],
                data["payment_date"],
                data["payment_type"],
                data.get("notes"),
            ),
        )
        cur.execute(
            """
            UPDATE incoming_stock
            SET amount_paid = COALESCE(amount_paid, 0) + %s,
                payment_status = CASE
                    WHEN (COALESCE(amount_paid, 0) + %s) >= amount THEN 'paid'
                    WHEN (COALESCE(amount_paid, 0) + %s) > 0       THEN 'partial'
                    ELSE 'pending'
                END
            WHERE id = %s
        """,
            (data["amount"], data["amount"], data["amount"], stock_id),
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def delete_payment(payment_id):
        """
        Deletes a payment and reverses its amount from the parent stock.
        Returns None if the payment doesn't exist (router will raise 404).
        GREATEST(0, ...) ensures amount_paid never goes below zero.
        """
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT stock_id, amount FROM payment_transactions WHERE id = %s",
            (payment_id,),
        )
        payment = cur.fetchone()
        if payment is None:
            cur.close()
            conn.close()
            return None  # Signal "not found" to the router

        stock_id, amount = payment["stock_id"], payment["amount"]
        cur.execute("DELETE FROM payment_transactions WHERE id = %s", (payment_id,))
        cur.execute(
            """
            UPDATE incoming_stock
            SET amount_paid = GREATEST(0, COALESCE(amount_paid, 0) - %s),
                payment_status = CASE
                    WHEN (GREATEST(0, COALESCE(amount_paid, 0) - %s)) >= amount THEN 'paid'
                    WHEN (GREATEST(0, COALESCE(amount_paid, 0) - %s)) > 0       THEN 'partial'
                    ELSE 'pending'
                END
            WHERE id = %s
        """,
            (amount, amount, amount, stock_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
