
from model.model import (
    IncomingStockModel, OutgoingStockModel, PaymentTransactionModel,
    SalesPaymentModel, ProductDetailModel
)
from database.database import SessionLocal
from sqlalchemy import text, or_, func
import base64
import os
import json
import requests
from datetime import datetime

# Helper to decode base64
def decode_photo(photo_str):
    if not photo_str or photo_str.startswith("http"):
        return None
    try:
        if "," in photo_str:
            photo_str = photo_str.split(",")[1]
        return base64.b64decode(photo_str)
    except Exception as e:
        print(f"Error decoding base64: {e}")
        return None

# Helper to encode blob back to plain base64 string
# The HTML already prepends 'data:image/jpeg;base64,' so we only return the raw encoded string
def encode_photo(blob_data):
    if not blob_data:
        return None
    return base64.b64encode(blob_data).decode('utf-8')

# Helper to convert ORM object to dict with photos converted
def to_dict(obj, is_sale=False):
    if not obj:
        return None
    d = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    # Safely format photos
    if 'product_photo' in d and d['product_photo']:
        d['product_photo'] = encode_photo(d['product_photo'])
    if 'bill_photo' in d and d['bill_photo']:
        d['bill_photo'] = encode_photo(d['bill_photo'])
    if not is_sale and 'bilti_photo' in d and d['bilti_photo']:
        d['bilti_photo'] = encode_photo(d['bilti_photo'])
    return d

class Dashboard:
    @staticmethod
    def get_stats():
        from database.database import SessionLocal
        with SessionLocal() as db:
            in_count = db.query(IncomingStockModel).count()
            in_discount = db.query(func.sum(IncomingStockModel.discount_amount)).scalar() or 0

            out_count = db.query(OutgoingStockModel).count()
            out_amount = db.query(func.sum(OutgoingStockModel.total_amount)).scalar() or 0
            out_discount = db.query(func.sum(OutgoingStockModel.discount_amount)).scalar() or 0

            # Last 5 entries for the dashboard recent lists
            recent_in = db.query(IncomingStockModel).order_by(IncomingStockModel.id.desc()).limit(5).all()
            recent_out = db.query(OutgoingStockModel).order_by(OutgoingStockModel.id.desc()).limit(5).all()

            return {
                # Flat keys that index.html reads directly
                "total_incoming": in_count,
                "total_outgoing": out_count,
                "total_sales_amount": float(out_amount),
                "total_discount_received": float(in_discount),
                "total_discount_given": float(out_discount),
                "recent_incoming": [
                    {
                        "product_name": r.product_name,
                        "source_name": r.source_name or "-",
                        "date_of_purchase": r.date_of_purchase,
                        "amount": r.amount or 0
                    }
                    for r in recent_in
                ],
                "recent_outgoing": [
                    {
                        "product_name": r.product_name,
                        "customer_name": r.customer_name or "-",
                        "date_of_sale": r.date_of_sale,
                        "total_amount": r.total_amount or 0
                    }
                    for r in recent_out
                ]
            }


class IncomingStock:
    @staticmethod
    def get_all():
        with SessionLocal() as db:
            rows = db.query(IncomingStockModel).order_by(IncomingStockModel.date_of_purchase.desc()).all()
            return [to_dict(r) for r in rows]

    @staticmethod
    def get_by_id(stock_id: int):
        with SessionLocal() as db:
            row = db.get(IncomingStockModel, stock_id)
            return to_dict(row)

    @staticmethod
    def search(term: str):
        with SessionLocal() as db:
            query = f"%{term}%"
            rows = db.query(IncomingStockModel).filter(
                or_(IncomingStockModel.product_name.like(query), IncomingStockModel.source_name.like(query))
            ).order_by(IncomingStockModel.date_of_purchase.desc()).all()
            return [to_dict(r) for r in rows]

    @staticmethod
    def create(data: dict):
        with SessionLocal() as db:
            # Process photos explicitly
            keys = ["product_photo", "bill_photo", "bilti_photo"]
            for k in keys:
                if k in data and data[k]:
                    data[k] = decode_photo(data[k])
            
            # Auto-calculate amount
            qty = data.get("quantity", 0)
            price = data.get("price_per_unit", 0)
            tax_pct = data.get("tax_percent", 0)
            discount = data.get("discount_amount", 0)
            subtotal = (qty * price) - discount
            tax_amount = subtotal * (tax_pct / 100)
            data["tax_amount"] = tax_amount
            data["amount"] = subtotal + tax_amount
            
            stock = IncomingStockModel(**data)
            db.add(stock)
            db.commit()
            db.refresh(stock)
            return stock.id

    @staticmethod
    def update(stock_id: int, data: dict):
        with SessionLocal() as db:
            stock = db.get(IncomingStockModel, stock_id)
            if not stock: return None

            # Handle photo fields carefully so we never accidentally delete an existing photo
            for k in ["product_photo", "bill_photo", "bilti_photo"]:
                if k in data:
                    if data[k] == "delete":
                        data[k] = None  # User explicitly wants to remove the photo
                    elif data[k]:  # User uploaded a new photo (plain base64 string)
                        data[k] = base64.b64decode(data[k])
                    else:
                        data.pop(k)  # No new photo uploaded — keep the existing one in DB

            # Apply all changes to the stock object
            for k, v in data.items():
                setattr(stock, k, v)

            # Recalculate the total amount
            subtotal = (stock.quantity * stock.price_per_unit) - stock.discount_amount
            stock.tax_amount = subtotal * (stock.tax_percent / 100)
            stock.amount = subtotal + stock.tax_amount

            db.commit()
            return True

    @staticmethod
    def delete(stock_id: int):
        with SessionLocal() as db:
            stock = db.get(IncomingStockModel, stock_id)
            if stock:
                db.delete(stock)
                db.commit()

    @staticmethod
    def get_payments(stock_id: int):
        with SessionLocal() as db:
            rows = db.query(PaymentTransactionModel).filter(PaymentTransactionModel.stock_id == stock_id).all()
            return [{"id": r.id, "amount": r.amount, "payment_date": r.payment_date, "payment_type": r.payment_type, "notes": r.notes} for r in rows]

    @staticmethod
    def add_payment(stock_id: int, data: dict):
        with SessionLocal() as db:
            stock = db.get(IncomingStockModel, stock_id)
            if not stock: return
            
            payment = PaymentTransactionModel(stock_id=stock_id, **data)
            db.add(payment)
            
            stock.amount_paid += data.get("amount", 0)
            if stock.amount_paid >= stock.amount:
                stock.payment_status = "paid"
            elif stock.amount_paid > 0:
                stock.payment_status = "partial"
            else:
                stock.payment_status = "pending"
                
            db.commit()

    @staticmethod
    def delete_payment(payment_id: int):
        with SessionLocal() as db:
            payment = db.get(PaymentTransactionModel, payment_id)
            if not payment: return None
            
            stock_id = payment.stock_id
            amt = payment.amount
            db.delete(payment)
            
            stock = db.get(IncomingStockModel, stock_id)
            if stock:
                stock.amount_paid = max(0, stock.amount_paid - amt)
                if stock.amount_paid >= stock.amount:
                    stock.payment_status = "paid"
                elif stock.amount_paid > 0:
                    stock.payment_status = "partial"
                else:
                    stock.payment_status = "pending"
            db.commit()
            return True


class OutgoingStock:
    @staticmethod
    def get_all():
        with SessionLocal() as db:
            rows = db.query(OutgoingStockModel).order_by(OutgoingStockModel.date_of_sale.desc()).all()
            return [to_dict(r, True) for r in rows]

    @staticmethod
    def get_by_id(stock_id: int):
        with SessionLocal() as db:
            row = db.get(OutgoingStockModel, stock_id)
            return to_dict(row, True)

    @staticmethod
    def search(term: str):
        with SessionLocal() as db:
            query = f"%{term}%"
            rows = db.query(OutgoingStockModel).filter(
                or_(OutgoingStockModel.product_name.like(query), OutgoingStockModel.customer_name.like(query), OutgoingStockModel.invoice_no.like(query))
            ).order_by(OutgoingStockModel.date_of_sale.desc()).all()
            return [to_dict(r, True) for r in rows]

    @staticmethod
    def create(data: dict):
        with SessionLocal() as db:
            if not data.get("invoice_no"):
                year = datetime.now().year
                # Sort by ID (integer) instead of invoice_no (string) to avoid ordering bugs with large numbers
                last = db.query(OutgoingStockModel).filter(
                    OutgoingStockModel.invoice_no.like(f"INV-{year}-%")
                ).order_by(OutgoingStockModel.id.desc()).first()
                if last and last.invoice_no:
                    try:
                        num = int(last.invoice_no.split("-")[-1]) + 1
                    except:
                        num = 1
                else:
                    num = 1
                data["invoice_no"] = f"INV-{year}-{num:04d}"

            keys = ["product_photo", "bill_photo"]
            for k in keys:
                if k in data and data[k]:
                    data[k] = decode_photo(data[k])
                    
            data["amount_paid"] = 0
            data["payment_status"] = "pending"
            
            stock = OutgoingStockModel(**data)
            db.add(stock)
            db.commit()
            db.refresh(stock)
            return stock.id

    @staticmethod
    def update(stock_id: int, data: dict):
        with SessionLocal() as db:
            stock = db.get(OutgoingStockModel, stock_id)
            if not stock: return None

            # Handle photo fields carefully so we never accidentally delete an existing photo
            for k in ["product_photo", "bill_photo"]:
                if k in data:
                    if data[k] == "delete":
                        data[k] = None  # User explicitly wants to remove photo
                    elif data[k]:  # User uploaded a new photo (plain base64 string)
                        data[k] = base64.b64decode(data[k])
                    else:
                        data.pop(k)  # No new photo uploaded — keep the existing one in DB

            # Apply all changes to the stock object
            for k, v in data.items():
                setattr(stock, k, v)

            db.commit()
            return True

    @staticmethod
    def delete(stock_id: int):
        with SessionLocal() as db:
            stock = db.get(OutgoingStockModel, stock_id)
            if stock:
                db.delete(stock)
                db.commit()

    @staticmethod
    def get_payments(stock_id: int):
        with SessionLocal() as db:
            rows = db.query(SalesPaymentModel).filter(SalesPaymentModel.stock_id == stock_id).all()
            return [{"id": r.id, "amount": r.amount, "payment_date": r.payment_date, "payment_type": r.payment_type, "notes": r.notes} for r in rows]

    @staticmethod
    def add_payment(stock_id: int, data: dict):
        with SessionLocal() as db:
            stock = db.get(OutgoingStockModel, stock_id)
            if not stock: return
            
            payment = SalesPaymentModel(stock_id=stock_id, **data)
            db.add(payment)
            
            stock.amount_paid += data.get("amount", 0)
            if stock.amount_paid >= stock.total_amount:
                stock.payment_status = "paid"
            elif stock.amount_paid > 0:
                stock.payment_status = "partial"
            else:
                stock.payment_status = "pending"
                
            db.commit()

    @staticmethod
    def delete_payment(payment_id: int):
        with SessionLocal() as db:
            payment = db.get(SalesPaymentModel, payment_id)
            if not payment: return None
            
            stock_id = payment.stock_id
            amt = payment.amount
            db.delete(payment)
            
            stock = db.get(OutgoingStockModel, stock_id)
            if stock:
                stock.amount_paid = max(0, stock.amount_paid - amt)
                if stock.amount_paid >= stock.total_amount:
                    stock.payment_status = "paid"
                elif stock.amount_paid > 0:
                    stock.payment_status = "partial"
                else:
                    stock.payment_status = "pending"
            db.commit()
            return True


class LiveInventory:
    @staticmethod
    def get_all():
        from database.database import SessionLocal, engine
        with SessionLocal() as db:
            # Reusing the existing SQLite view using text
            sql = """
            SELECT
                li.product_name,
                li.current_stock,
                li.unit,
                pd.details,
                (SELECT product_photo FROM incoming_stock WHERE product_name = li.product_name AND product_photo IS NOT NULL ORDER BY date_of_purchase DESC LIMIT 1) AS product_photo,
                (SELECT GROUP_CONCAT(DISTINCT source_name) FROM incoming_stock WHERE product_name = li.product_name AND source_name IS NOT NULL) AS source_name
            FROM live_inventory li
            LEFT JOIN product_details pd ON li.product_name = pd.product_name
            ORDER BY li.product_name;
            """
            result = db.execute(text(sql)).fetchall()
            ret = []
            for row in result:
                d = {
                    "product_name": row[0],
                    "current_stock": row[1],
                    "unit": row[2],
                    "details": row[3],
                    "product_photo": encode_photo(row[4]) if row[4] else None,
                    "source_name": row[5]
                }
                ret.append(d)
            return ret

    @staticmethod
    def get_low_stock(threshold: float = 5.0):
        """Return products whose current stock is at or below the threshold."""
        with SessionLocal() as db:
            sql = """
            SELECT product_name, current_stock, unit
            FROM live_inventory
            WHERE current_stock <= :threshold
            ORDER BY current_stock ASC
            """
            result = db.execute(text(sql), {"threshold": threshold}).fetchall()
            # Build a simple list of dicts
            return [
                {"product_name": row[0], "current_stock": row[1], "unit": row[2]}
                for row in result
            ]

    @staticmethod
    def update_details(product_name: str, details: str):
        with SessionLocal() as db:
            row = db.get(ProductDetailModel, product_name)
            if row:
                row.details = details
            else:
                row = ProductDetailModel(product_name=product_name, details=details)
                db.add(row)
            db.commit()

def scan_bill_image(base64_image: str, suggested_type: str = "generic"):
    """Send the image to Gemini Vision API and extract bill data."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"success": False, "error": "GEMINI_API_KEY is not set in your .env file."}

    # Strip the data URI prefix if present (e.g. 'data:image/jpeg;base64,...')
    if "," in base64_image:
        base64_image = base64_image.split(",")[1]

    # The prompt tells Gemini exactly what to extract
    prompt = f"""
    You are a bill/invoice reader. Look at this {suggested_type} bill image and extract the following fields.
    Reply ONLY with a valid JSON object — no markdown, no explanation.

    Fields to extract:
    - bill_type: "incoming" if it's a purchase/supplier bill, "outgoing" if it's a sales/customer invoice
    - confidence: a number between 0 and 1 indicating how confident you are
    - data: an object containing:
        - product_name: name of the main product
        - supplier_name: supplier or seller name (for incoming bills)
        - customer_name: customer or buyer name (for outgoing bills)
        - date: the bill date in YYYY-MM-DD format
        - quantity: the quantity (number only)
        - unit: unit of measurement (pcs, kg, mtr, roll, box, etc.)
        - price_per_unit: price per unit (number only)
        - tax_percentage: GST or tax percentage (number only)
        - total_amount: final total amount (number only)
        - gst_number: GST number if present
        - invoice_number: invoice number if present

    If any field is missing or unclear, use null for that field.
    """

    # Build the Gemini API request body
    request_body = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64_image
                    }
                }
            ]
        }]
    }

    # Call the Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    try:
        response = requests.post(url, json=request_body, timeout=30)
        response.raise_for_status()
    except Exception as e:
        return {"success": False, "error": f"Gemini API call failed: {str(e)}"}

    # Parse the Gemini response
    try:
        raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        # Clean up any markdown fences Gemini might have added
        clean_text = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        extracted = json.loads(clean_text)
        extracted["success"] = True
        return extracted
    except Exception as e:
        return {"success": False, "error": f"Could not parse Gemini response: {str(e)}"}