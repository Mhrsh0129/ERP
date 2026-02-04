from db_config import get_db_connection
from mysql.connector import Error
from datetime import date, datetime
import base64


class IncomingStock:
    @staticmethod
    def get_all():
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, product_name, source_name, date_of_purchase, 
                       quantity, unit, price_per_unit, tax_percent, discount_amount, tax_amount, amount,
                       payment_status, amount_paid, payment_type, payment_date, delivery_date,
                       product_photo, bill_photo, bilti_photo
                FROM incoming_stock 
                ORDER BY date_of_purchase DESC
            """)
            results = cursor.fetchall()

            for row in results:
                # Handle photo fields
                for photo_field in ["product_photo", "bill_photo", "bilti_photo"]:
                    if row.get(photo_field):
                        row[photo_field] = base64.b64encode(row[photo_field]).decode(
                            "utf-8"
                        )
                # Handle date fields
                for key in ["date_of_purchase", "payment_date", "delivery_date"]:
                    if row.get(key) and isinstance(row[key], date):
                        row[key] = row[key].isoformat()

            cursor.close()
            conn.close()
            return {"success": True, "data": results}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_by_id(stock_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, product_name, source_name, date_of_purchase, 
                       quantity, unit, price_per_unit, tax_percent, discount_amount, tax_amount, amount,
                       payment_status, amount_paid, payment_type, payment_date, delivery_date,
                       product_photo, bill_photo, bilti_photo
                FROM incoming_stock 
                WHERE id = %s
            """,
                (stock_id,),
            )
            result = cursor.fetchone()

            if result:
                # Handle photo fields
                for photo_field in ["product_photo", "bill_photo", "bilti_photo"]:
                    if result.get(photo_field):
                        result[photo_field] = base64.b64encode(
                            result[photo_field]
                        ).decode("utf-8")
                # Handle date fields
                for key in ["date_of_purchase", "payment_date", "delivery_date"]:
                    if result.get(key) and isinstance(result[key], date):
                        result[key] = result[key].isoformat()

            cursor.close()
            conn.close()
            return {"success": True, "data": result}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def create(data):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Handle photo uploads
            product_photo = None
            bill_photo = None
            bilti_photo = None

            if "product_photo" in data and data["product_photo"]:
                product_photo = base64.b64decode(data["product_photo"])
            if "bill_photo" in data and data["bill_photo"]:
                bill_photo = base64.b64decode(data["bill_photo"])
            if "bilti_photo" in data and data["bilti_photo"]:
                bilti_photo = base64.b64decode(data["bilti_photo"])

            # Note: 'amount' and 'tax_amount' are generated columns, so we don't insert them
            cursor.execute(
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
                    data["source_name"],
                    data["date_of_purchase"],
                    data.get("quantity"),  # NULL if not provided
                    data.get("unit"),  # NULL if not provided
                    data.get("price_per_unit"),  # NULL if not provided
                    data.get("tax_percent"),  # NULL if not provided
                    data.get("discount_amount", 0.00),
                    data.get("payment_status"),  # NULL if not provided
                    data.get("amount_paid"),  # NULL if not provided
                    data.get("payment_type"),  # NULL if not provided
                    data.get("payment_date"),
                    data.get("delivery_date"),
                    product_photo,
                    bill_photo,
                    bilti_photo,
                ),
            )

            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return {
                "success": True,
                "id": new_id,
                "message": "Stock added successfully",
            }
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update(stock_id, data):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Handle photo uploads
            photo_updates = {}
            for photo_field in ["product_photo", "bill_photo", "bilti_photo"]:
                if photo_field in data and data[photo_field]:
                    if data[photo_field].startswith("data:"):
                        photo_updates[photo_field] = base64.b64decode(
                            data[photo_field].split(",")[1]
                        )
                    else:
                        photo_updates[photo_field] = base64.b64decode(data[photo_field])

            # Build update query
            if photo_updates:
                cursor.execute(
                    """
                    UPDATE incoming_stock 
                    SET product_name=%s, source_name=%s, date_of_purchase=%s, 
                        quantity=%s, unit=%s, price_per_unit=%s, tax_percent=%s, discount_amount=%s,
                        payment_status=%s, amount_paid=%s, payment_type=%s, payment_date=%s, delivery_date=%s,
                        product_photo=%s, bill_photo=%s, bilti_photo=%s
                    WHERE id=%s
                """,
                    (
                        data["product_name"],
                        data["source_name"],
                        data["date_of_purchase"],
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
                        photo_updates.get("product_photo"),
                        photo_updates.get("bill_photo"),
                        photo_updates.get("bilti_photo"),
                        stock_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE incoming_stock 
                    SET product_name=%s, source_name=%s, date_of_purchase=%s, 
                        quantity=%s, unit=%s, price_per_unit=%s, tax_percent=%s, discount_amount=%s,
                        payment_status=%s, amount_paid=%s, payment_type=%s, payment_date=%s, delivery_date=%s
                    WHERE id=%s
                """,
                    (
                        data["product_name"],
                        data["source_name"],
                        data["date_of_purchase"],
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
                        stock_id,
                    ),
                )

            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True, "message": "Stock updated successfully"}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def add_payment(stock_id, data):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. Insert payment record
            cursor.execute(
                """
                INSERT INTO payment_transactions 
                (stock_id, amount, payment_date, payment_type, notes)
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

            # 2. Update parent stock amount_paid
            cursor.execute(
                """
                UPDATE incoming_stock 
                SET amount_paid = COALESCE(amount_paid, 0) + %s,
                    payment_status = CASE 
                        WHEN (COALESCE(amount_paid, 0) + %s) >= amount THEN 'paid'
                        WHEN (COALESCE(amount_paid, 0) + %s) > 0 THEN 'partial'
                        ELSE 'pending'
                    END
                WHERE id = %s
            """,
                (data["amount"], data["amount"], data["amount"], stock_id),
            )

            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_payments(stock_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, amount, payment_date, payment_type, notes, created_at
                FROM payment_transactions
                WHERE stock_id = %s
                ORDER BY payment_date DESC
            """,
                (stock_id,),
            )
            results = cursor.fetchall()

            # Format dates
            for row in results:
                if row.get("payment_date") and isinstance(row["payment_date"], date):
                    row["payment_date"] = row["payment_date"].isoformat()
                if row.get("created_at") and isinstance(row["created_at"], datetime):
                    row["created_at"] = row["created_at"].isoformat()

            cursor.close()
            conn.close()
            return {"success": True, "data": results}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_payment(payment_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # 1. Get payment details first to revert amount
            cursor.execute(
                "SELECT stock_id, amount FROM payment_transactions WHERE id = %s",
                (payment_id,),
            )
            payment = cursor.fetchone()

            if not payment:
                return {"success": False, "error": "Payment not found"}

            stock_id = payment["stock_id"]
            amount = payment["amount"]

            # 2. Delete payment record
            cursor.execute(
                "DELETE FROM payment_transactions WHERE id = %s", (payment_id,)
            )

            # 3. Update parent stock amount_paid
            cursor.execute(
                """
                UPDATE incoming_stock 
                SET amount_paid = GREATEST(0, COALESCE(amount_paid, 0) - %s),
                    payment_status = CASE 
                        WHEN (GREATEST(0, COALESCE(amount_paid, 0) - %s)) >= amount THEN 'paid'
                        WHEN (GREATEST(0, COALESCE(amount_paid, 0) - %s)) > 0 THEN 'partial'
                        ELSE 'pending'
                    END
                WHERE id = %s
            """,
                (amount, amount, amount, stock_id),
            )

            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete(stock_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incoming_stock WHERE id = %s", (stock_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True, "message": "Stock deleted successfully"}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def search(query):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            search_pattern = f"%{query}%"
            cursor.execute(
                """
                SELECT id, product_name, source_name, date_of_purchase, 
                       quantity, unit, price_per_unit, tax_percent, tax_amount, amount,
                       payment_status, amount_paid, payment_type, payment_date, delivery_date,
                       product_photo, bill_photo, bilti_photo
                FROM incoming_stock 
                WHERE product_name LIKE %s OR source_name LIKE %s
                ORDER BY date_of_purchase DESC
            """,
                (search_pattern, search_pattern),
            )
            results = cursor.fetchall()

            for row in results:
                # Handle photo fields
                for photo_field in ["product_photo", "bill_photo", "bilti_photo"]:
                    if row.get(photo_field):
                        row[photo_field] = base64.b64encode(row[photo_field]).decode(
                            "utf-8"
                        )
                # Handle date fields
                for key in ["date_of_purchase", "payment_date", "delivery_date"]:
                    if row.get(key) and isinstance(row[key], date):
                        row[key] = row[key].isoformat()

            cursor.close()
            conn.close()
            return {"success": True, "data": results}
        except Error as e:
            return {"success": False, "error": str(e)}


class OutgoingStock:
    @staticmethod
    def get_all():
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, invoice_no, product_name, customer_name, gst_number, date_of_sale, 
                       quantity, unit, price_per_unit, total_amount, tax, tax_percentage, discount_amount,
                       payment_status, amount_paid, payment_type, payment_date, delivery_date,
                       bill_photo, product_photo
                FROM outgoing_stock 
                ORDER BY date_of_sale DESC
            """)
            results = cursor.fetchall()

            for row in results:
                # Handle photo fields
                for photo_field in ["bill_photo", "product_photo"]:
                    if row.get(photo_field):
                        row[photo_field] = base64.b64encode(row[photo_field]).decode(
                            "utf-8"
                        )

                for key in ["date_of_sale", "payment_date", "delivery_date"]:
                    if row.get(key) and isinstance(row[key], date):
                        row[key] = row[key].isoformat()

            cursor.close()
            conn.close()
            return {"success": True, "data": results}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_by_id(stock_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, invoice_no, product_name, customer_name, gst_number, date_of_sale, 
                       quantity, unit, price_per_unit, total_amount, tax, tax_percentage, discount_amount,
                       payment_status, amount_paid, payment_type, payment_date, delivery_date,
                       bill_photo, product_photo
                FROM outgoing_stock 
                WHERE id = %s
            """,
                (stock_id,),
            )
            result = cursor.fetchone()

            if result:
                for photo_field in ["bill_photo", "product_photo"]:
                    if result.get(photo_field):
                        result[photo_field] = base64.b64encode(
                            result[photo_field]
                        ).decode("utf-8")

                for key in ["date_of_sale", "payment_date", "delivery_date"]:
                    if result.get(key) and isinstance(result[key], date):
                        result[key] = result[key].isoformat()

            cursor.close()
            conn.close()
            return {"success": True, "data": result}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def create(data):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            print(f"DEBUG: OutgoingStock.create received data: {data}")  # Debug log

            photo_data = None
            if "bill_photo" in data and data["bill_photo"]:
                if data["bill_photo"].startswith("data:"):
                    photo_data = base64.b64decode(data["bill_photo"].split(",")[1])
                else:
                    photo_data = base64.b64decode(data["bill_photo"])

            product_photo_data = None
            if "product_photo" in data and data["product_photo"]:
                if data["product_photo"].startswith("data:"):
                    product_photo_data = base64.b64decode(
                        data["product_photo"].split(",")[1]
                    )
                else:
                    product_photo_data = base64.b64decode(data["product_photo"])

            # Calculate amount if not provided
            total_amount = data["total_amount"]

            # Auto-generate invoice number if not provided
            invoice_no = data.get("invoice_no", "").strip()
            if not invoice_no:
                # Get current year
                from datetime import datetime

                current_year = datetime.now().year

                # Find the highest invoice number for this year
                cursor.execute(
                    """
                    SELECT invoice_no FROM outgoing_stock 
                    WHERE invoice_no LIKE %s 
                    ORDER BY invoice_no DESC LIMIT 1
                """,
                    (f"INV-{current_year}-%",),
                )

                last_invoice = cursor.fetchone()

                if last_invoice and last_invoice[0]:
                    # Extract the number part and increment
                    try:
                        last_num = int(last_invoice[0].split("-")[-1])
                        next_num = last_num + 1
                    except (ValueError, IndexError):
                        next_num = 1
                else:
                    next_num = 1

                invoice_no = f"INV-{current_year}-{next_num:03d}"
                print(f"DEBUG: Auto-generated invoice number: {invoice_no}")

            # Handle optional payment type
            payment_type = data.get("payment_type")
            if not payment_type:
                payment_type = None

            cursor.execute(
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
                    data["customer_name"],
                    data.get("gst_number", ""),
                    data["date_of_sale"],
                    data.get("quantity", 1),
                    data.get("unit", "pcs"),
                    data.get("price_per_unit", 0),
                    total_amount,
                    data.get("tax", 0),
                    data.get("tax_percentage", 5.00),
                    data.get("discount_amount", 0.00),
                    payment_type,
                    data.get("payment_date") or None,
                    data.get("delivery_date") or None,
                    photo_data,
                    product_photo_data,
                ),
            )

            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return {
                "success": True,
                "id": new_id,
                "message": "Stock added successfully",
            }
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update(stock_id, data):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            print(f"DEBUG: OutgoingStock.update received data: {data}")  # Debug log

            # Handle photo update if provided
            photo_update_sql = ""
            params = [
                data.get("invoice_no", ""),
                data["product_name"],
                data["customer_name"],
                data.get("gst_number", ""),
                data["date_of_sale"],
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

            if "bill_photo" in data and data["bill_photo"]:
                photo_update_sql += ", bill_photo=%s"
                if data["bill_photo"].startswith("data:"):
                    params.append(base64.b64decode(data["bill_photo"].split(",")[1]))
                else:
                    params.append(base64.b64decode(data["bill_photo"]))

            if "product_photo" in data and data["product_photo"]:
                photo_update_sql += ", product_photo=%s"
                if data["product_photo"].startswith("data:"):
                    product_photo_data = base64.b64decode(
                        data["product_photo"].split(",")[1]
                    )
                    params.append(product_photo_data)
                else:
                    product_photo_data = base64.b64decode(data["product_photo"])
                    params.append(product_photo_data)

            # Add ID to params
            params.append(stock_id)

            sql_query = f"""
                UPDATE outgoing_stock 
                SET invoice_no=%s, product_name=%s, customer_name=%s, gst_number=%s, date_of_sale=%s, 
                    quantity=%s, unit=%s, price_per_unit=%s, total_amount=%s, tax=%s, tax_percentage=%s, discount_amount=%s,
                    payment_type=%s, payment_date=%s, delivery_date=%s
                    {photo_update_sql}
                WHERE id=%s
            """

            print(f"DEBUG: Executing SQL: {sql_query}")
            print(f"DEBUG: With params: {params}")

            cursor.execute(sql_query, tuple(params))

            rows_affected = cursor.rowcount
            print(f"DEBUG: Rows affected: {rows_affected}")

            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True, "message": "Sale updated successfully!"}
        except Error as e:
            print(f"DEBUG ERROR in update: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete(stock_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM outgoing_stock WHERE id = %s", (stock_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True, "message": "Stock deleted successfully"}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def search(query):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            search_pattern = f"%{query}%"
            cursor.execute(
                """
                SELECT id, invoice_no, product_name, customer_name, date_of_sale, 
                       quantity, unit, price_per_unit, total_amount,
                       payment_status, amount_paid, payment_type, payment_date, 
                       bill_photo, product_photo
                FROM outgoing_stock 
                WHERE product_name LIKE %s OR customer_name LIKE %s OR invoice_no LIKE %s
                ORDER BY date_of_sale DESC
            """,
                (search_pattern, search_pattern, search_pattern),
            )
            results = cursor.fetchall()

            for row in results:
                for photo_field in ["bill_photo", "product_photo"]:
                    if row.get(photo_field):
                        row[photo_field] = base64.b64encode(row[photo_field]).decode(
                            "utf-8"
                        )

                for key in ["date_of_sale", "payment_date"]:
                    if row.get(key) and isinstance(row[key], date):
                        row[key] = row[key].isoformat()

            cursor.close()
            conn.close()
            return {"success": True, "data": results}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def add_payment(stock_id, data):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. Insert payment record
            cursor.execute(
                """
                INSERT INTO sales_payments 
                (stock_id, amount, payment_date, payment_type, notes)
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

            # 2. Update parent stock amount_paid
            cursor.execute(
                """
                UPDATE outgoing_stock 
                SET amount_paid = COALESCE(amount_paid, 0) + %s,
                    payment_status = CASE 
                        WHEN (COALESCE(amount_paid, 0) + %s) >= total_amount THEN 'paid'
                        WHEN (COALESCE(amount_paid, 0) + %s) > 0 THEN 'partial'
                        ELSE 'pending'
                    END
                WHERE id = %s
            """,
                (data["amount"], data["amount"], data["amount"], stock_id),
            )

            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_payments(stock_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, amount, payment_date, payment_type, notes, created_at
                FROM sales_payments
                WHERE stock_id = %s
                ORDER BY payment_date DESC
            """,
                (stock_id,),
            )
            results = cursor.fetchall()

            # Format dates
            for row in results:
                if row.get("payment_date") and isinstance(row["payment_date"], date):
                    row["payment_date"] = row["payment_date"].isoformat()
                if row.get("created_at") and isinstance(row["created_at"], datetime):
                    row["created_at"] = row["created_at"].isoformat()

            cursor.close()
            conn.close()
            return {"success": True, "data": results}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_payment(payment_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # 1. Get payment details first to revert amount
            cursor.execute(
                "SELECT stock_id, amount FROM sales_payments WHERE id = %s",
                (payment_id,),
            )
            payment = cursor.fetchone()

            if not payment:
                return {"success": False, "error": "Payment not found"}

            stock_id = payment["stock_id"]
            amount = payment["amount"]

            # 2. Delete payment record
            cursor.execute("DELETE FROM sales_payments WHERE id = %s", (payment_id,))

            # 3. Update parent stock amount_paid
            cursor.execute(
                """
                UPDATE outgoing_stock 
                SET amount_paid = GREATEST(0, COALESCE(amount_paid, 0) - %s),
                    payment_status = CASE 
                        WHEN (GREATEST(0, COALESCE(amount_paid, 0) - %s)) >= total_amount THEN 'paid'
                        WHEN (GREATEST(0, COALESCE(amount_paid, 0) - %s)) > 0 THEN 'partial'
                        ELSE 'pending'
                    END
                WHERE id = %s
            """,
                (amount, amount, amount, stock_id),
            )

            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_low_stock():
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            # Since there's no reorder_level in the actual table, return empty for now
            cursor.close()
            conn.close()
            return {"success": True, "data": []}
        except Error as e:
            return {"success": False, "error": str(e)}


class LiveInventory:
    @staticmethod
    def get_all():
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Enhanced query to fetch Source (all suppliers), Photo (latest), and Details
            # We use GROUP_CONCAT to show all suppliers for products from multiple sources
            query = """
                SELECT 
                    li.product_name, 
                    li.current_stock, 
                    li.unit,
                    pd.details,
                    (SELECT product_photo FROM incoming_stock 
                     WHERE product_name = li.product_name 
                     AND product_photo IS NOT NULL 
                     ORDER BY date_of_purchase DESC LIMIT 1) as product_photo,
                     (SELECT GROUP_CONCAT(DISTINCT source_name ORDER BY source_name SEPARATOR ', ')
                     FROM incoming_stock 
                     WHERE product_name = li.product_name 
                     AND source_name IS NOT NULL) as source_name
                FROM live_inventory li
                LEFT JOIN product_details pd ON li.product_name = pd.product_name
                ORDER BY li.product_name
            """

            cursor.execute(query)
            results = cursor.fetchall()

            for row in results:
                # Handle photo encoding
                if row.get("product_photo"):
                    row["product_photo"] = base64.b64encode(
                        row["product_photo"]
                    ).decode("utf-8")

            cursor.close()
            conn.close()
            return {"success": True, "data": results}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_low_stock():
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            # Since there's no reorder_level in the actual table, return empty for now
            cursor.close()
            conn.close()
            return {"success": True, "data": []}
        except Error as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_details(product_name, details):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Upsert (Insert or Update) details
            cursor.execute(
                """
                INSERT INTO product_details (product_name, details) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE details = VALUES(details)
            """,
                (product_name, details),
            )

            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True, "message": "Details updated successfully"}
        except Error as e:
            return {"success": False, "error": str(e)}


class Dashboard:
    @staticmethod
    def get_stats():
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT COUNT(*) as total FROM incoming_stock")
            total_incoming = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM outgoing_stock")
            total_outgoing = cursor.fetchone()["total"]

            cursor.execute("SELECT SUM(amount) as total FROM incoming_stock")
            total_purchase = cursor.fetchone()["total"] or 0

            cursor.execute("SELECT SUM(total_amount) as total FROM outgoing_stock")
            total_sales = cursor.fetchone()["total"] or 0

            cursor.execute("SELECT SUM(discount_amount) as total FROM incoming_stock")
            total_discount_received = cursor.fetchone()["total"] or 0

            cursor.execute("SELECT SUM(discount_amount) as total FROM outgoing_stock")
            total_discount_given = cursor.fetchone()["total"] or 0

            low_stock_count = 0

            cursor.execute("""
                SELECT product_name, source_name, date_of_purchase, quantity, unit, price_per_unit, amount 
                FROM incoming_stock 
                ORDER BY date_of_purchase DESC 
                LIMIT 5
            """)
            recent_incoming = cursor.fetchall()
            for row in recent_incoming:
                if isinstance(row.get("date_of_purchase"), date):
                    row["date_of_purchase"] = row["date_of_purchase"].isoformat()

            cursor.execute("""
                SELECT product_name, customer_name, date_of_sale, total_amount 
                FROM outgoing_stock 
                ORDER BY date_of_sale DESC 
                LIMIT 5
            """)
            recent_outgoing = cursor.fetchall()
            for row in recent_outgoing:
                if isinstance(row.get("date_of_sale"), date):
                    row["date_of_sale"] = row["date_of_sale"].isoformat()
                # Rename total_amount to amount for frontend compatibility
                if "total_amount" in row:
                    row["amount"] = row["total_amount"]

            cursor.close()
            conn.close()

            return {
                "success": True,
                "data": {
                    "total_incoming": total_incoming,
                    "total_outgoing": total_outgoing,
                    "total_purchase_amount": float(total_purchase),
                    "total_sales_amount": float(total_sales),
                    "total_discount_received": float(total_discount_received),
                    "total_discount_given": float(total_discount_given),
                    "low_stock_count": low_stock_count,
                    "recent_incoming": recent_incoming,
                    "recent_outgoing": recent_outgoing,
                },
            }
        except Error as e:
            return {"success": False, "error": str(e)}
