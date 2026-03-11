"""
models/outgoing_stock.py — DB operations for the outgoing_stock table (sales).

Same structure as incoming_stock.py — functions return plain data, no wrapping.
"""

from app.core.database import get_db_connection
from datetime import date, datetime
import base64


def encode_photos(row, fields=("bill_photo", "product_photo")):
    """Converts BLOB bytes to base64 strings for JSON transport."""
    for f in fields:
        if row.get(f):
            row[f] = base64.b64encode(row[f]).decode("utf-8")


def format_dates(row, keys=("date_of_sale", "payment_date", "delivery_date")):
    """Converts date/datetime objects to ISO strings for JSON transport."""
    for k in keys:
        if row.get(k) and isinstance(row[k], (date, datetime)):
            row[k] = row[k].isoformat()


def decode_photo(val):
    """Strips data URI prefix if present, then decodes base64 to bytes."""
    if not val:
        return None
    raw = val.split(",")[1] if "," in val else val
    return base64.b64decode(raw)


class OutgoingStock:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id, invoice_no, product_name, customer_name, gst_number, date_of_sale,
                   quantity, unit, price_per_unit, total_amount, tax, tax_percentage, discount_amount,
                   payment_status, amount_paid, payment_type, payment_date, delivery_date,
                   bill_photo, product_photo
            FROM outgoing_stock ORDER BY date_of_sale DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for row in rows:
            encode_photos(row)
            format_dates(row)
        return rows

    @staticmethod
    def get_by_id(stock_id):
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, invoice_no, product_name, customer_name, gst_number, date_of_sale,
                   quantity, unit, price_per_unit, total_amount, tax, tax_percentage, discount_amount,
                   payment_status, amount_paid, payment_type, payment_date, delivery_date,
                   bill_photo, product_photo
            FROM outgoing_stock WHERE id = %s
        """,
            (stock_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            encode_photos(row)
            format_dates(row)
        return row

    @staticmethod
    def search(query):
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        pattern = f"%{query}%"
        cur.execute(
            """
            SELECT id, invoice_no, product_name, customer_name, date_of_sale,
                   quantity, unit, price_per_unit, total_amount,
                   payment_status, amount_paid, payment_type, payment_date,
                   bill_photo, product_photo
            FROM outgoing_stock
            WHERE product_name LIKE %s OR customer_name LIKE %s OR invoice_no LIKE %s
            ORDER BY date_of_sale DESC
        """,
            (pattern, pattern, pattern),
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
        """Inserts a new sale. Auto-generates invoice_no if not provided. Returns new id."""
        conn = get_db_connection()
        cur = conn.cursor()

        # Auto-generate invoice number if the frontend didn't send one
        invoice_no = (data.get("invoice_no") or "").strip()
        if not invoice_no:
            from datetime import datetime

            year = datetime.now().year
            cur.execute(
                """
                SELECT invoice_no FROM outgoing_stock
                WHERE invoice_no LIKE %s ORDER BY invoice_no DESC LIMIT 1
            """,
                (f"INV-{year}-%",),
            )
            last = cur.fetchone()
            next_num = (int(last[0].split("-")[-1]) + 1) if (last and last[0]) else 1
            invoice_no = f"INV-{year}-{next_num:03d}"

        cur.execute(
            """
            INSERT INTO outgoing_stock
            (invoice_no, product_name, customer_name, gst_number, date_of_sale,
             quantity, unit, price_per_unit, total_amount, tax, tax_percentage, discount_amount,
             payment_type, payment_date, delivery_date, bill_photo, product_photo,
             amount_paid, payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 'pending')
        """,
            (
                invoice_no,
                data["product_name"],
                data.get("customer_name"),
                data.get("gst_number", ""),
                data.get("date_of_sale"),
                data.get("quantity", 1),
                data.get("unit", "pcs"),
                data.get("price_per_unit", 0),
                data["total_amount"],
                data.get("tax", 0),
                data.get("tax_percentage", 5.00),
                data.get("discount_amount", 0.00),
                data.get("payment_type") or None,
                data.get("payment_date") or None,
                data.get("delivery_date") or None,
                decode_photo(data.get("bill_photo")),
                decode_photo(data.get("product_photo")),
            ),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        return new_id

    @staticmethod
    def update(stock_id, data):
        conn = get_db_connection()
        cur = conn.cursor()

        params = [
            data.get("invoice_no", ""),
            data["product_name"],
            data.get("customer_name"),
            data.get("gst_number", ""),
            data.get("date_of_sale"),
            data.get("quantity", 1),
            data.get("unit", "pcs"),
            data.get("price_per_unit", 0),
            data["total_amount"],
            data.get("tax", 0),
            data.get("tax_percentage", 5.00),
            data.get("discount_amount", 0.00),
            data.get("payment_type") or None,
            data.get("payment_date") or None,
            data.get("delivery_date") or None,
        ]

        # Only include photo columns if new images were sent
        photo_sql = ""
        if data.get("bill_photo"):
            photo_sql += ", bill_photo=%s"
            params.append(decode_photo(data["bill_photo"]))
        if data.get("product_photo"):
            photo_sql += ", product_photo=%s"
            params.append(decode_photo(data["product_photo"]))

        params.append(stock_id)
        cur.execute(
            f"""
            UPDATE outgoing_stock
            SET invoice_no=%s, product_name=%s, customer_name=%s, gst_number=%s, date_of_sale=%s,
                quantity=%s, unit=%s, price_per_unit=%s, total_amount=%s, tax=%s,
                tax_percentage=%s, discount_amount=%s,
                payment_type=%s, payment_date=%s, delivery_date=%s
                {photo_sql}
            WHERE id=%s
        """,
            tuple(params),
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def delete(stock_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM outgoing_stock WHERE id = %s", (stock_id,))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def get_payments(stock_id):
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, amount, payment_date, payment_type, notes, created_at
            FROM sales_payments WHERE stock_id = %s ORDER BY payment_date DESC
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
        """Inserts a payment and updates amount_paid + payment_status on the parent sale."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sales_payments (stock_id, amount, payment_date, payment_type, notes)
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
            UPDATE outgoing_stock
            SET amount_paid = COALESCE(amount_paid, 0) + %s,
                payment_status = CASE
                    WHEN (COALESCE(amount_paid, 0) + %s) >= total_amount THEN 'paid'
                    WHEN (COALESCE(amount_paid, 0) + %s) > 0             THEN 'partial'
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
        """Returns None if payment not found (router raises 404). Otherwise deletes and reverses."""
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT stock_id, amount FROM sales_payments WHERE id = %s", (payment_id,)
        )
        payment = cur.fetchone()
        if payment is None:
            cur.close()
            conn.close()
            return None

        stock_id, amount = payment["stock_id"], payment["amount"]
        cur.execute("DELETE FROM sales_payments WHERE id = %s", (payment_id,))
        cur.execute(
            """
            UPDATE outgoing_stock
            SET amount_paid = GREATEST(0, COALESCE(amount_paid, 0) - %s),
                payment_status = CASE
                    WHEN (GREATEST(0, COALESCE(amount_paid, 0) - %s)) >= total_amount THEN 'paid'
                    WHEN (GREATEST(0, COALESCE(amount_paid, 0) - %s)) > 0             THEN 'partial'
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
