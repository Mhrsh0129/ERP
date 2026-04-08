"""
================================================================================
Jay Shree Traders - Core Business Logic Services
================================================================================

This file contains the "brain" of the ERP system. It handles all database operations
(Create, Read, Update, Delete) and external API integrations.

Why we use this structure:
1. Separation of Concerns: Main.py only handles HTTP routes. This file handles data logic.
2. SQLAlchemy ORM: We use SQLAlchemy instead of raw SQL because it prevents SQL Injection
   attacks, works perfectly with Python objects, and automatically converts data types.
3. Why not other options?: We could use pure Raw SQL (like sqlite3), but it becomes
   very messy to maintain. SQLAlchemy makes code clean, reliable, and easy to read.

================================================================================
"""

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

# ==============================================================================
# Helper Functions (Photo Handling & Conversions)
# ==============================================================================

def decode_photo(photo_str):
    """
    Converts a Base64 string from the frontend into raw bytes to store in the database.
    
    Why Base64 & BLOBs?: We store images directly in the SQLite database as BLOBs 
    (Binary Large Objects) instead of saving files to a physical folder like /images.
    Why not other options?: Local folders can get lost, and cloud storage (like Amazon S3) 
    costs money and requires internet. Storing as a BLOB keeps the entire ERP app 
    in a single lightweight inventory.db file!
    """
    if not photo_str or photo_str.startswith("http"):
        return None
    try:
        # Strip the data URI prefix (e.g., data:image/jpeg;base64,) sent by the browser
        if "," in photo_str:
            photo_str = photo_str.split(",")[1]
        return base64.b64decode(photo_str)
    except Exception as e:
        print(f"Error decoding base64: {e}")
        return None


def encode_photo(blob_data):
    """
    Converts raw bytes from the database back into a Base64 string for the frontend.
    The HTML image tags know how to read these base64 strings directly.
    """
    if not blob_data:
        return None
    return base64.b64encode(blob_data).decode('utf-8')


def to_dict(obj, is_sale=False):
    """
    Converts a database SQLAlchemy Object into a standard Python Dictionary.
    
    Why this method?: FastAPI automatically converts Python dictionaries into JSON 
    data for our frontend. We use this method to intercept the database object and
    smoothly encode the heavy photo bytes back into strings before sending.
    """
    if not obj:
        return None
    # Extract all columns dynamically
    d = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    
    # Safely format photos back to strings
    if 'product_photo' in d and d['product_photo']:
        d['product_photo'] = encode_photo(d['product_photo'])
    if 'bill_photo' in d and d['bill_photo']:
        d['bill_photo'] = encode_photo(d['bill_photo'])
    if not is_sale and 'bilti_photo' in d and d['bilti_photo']:
        d['bilti_photo'] = encode_photo(d['bilti_photo'])
    return d


# ==============================================================================
# Dashboard Service
# ==============================================================================
class Dashboard:
    @staticmethod
    def get_stats():
        """
        Calculates all key metrics (totals, counts, discounts) to display on the 
        main dashboard instantly. Returns the 5 most recent activities too.
        """
        with SessionLocal() as db:
            # Aggregate queries using func.sum() are extremely fast in SQL
            in_count = db.query(IncomingStockModel).count()
            in_discount = db.query(func.sum(IncomingStockModel.discount_amount)).scalar() or 0

            out_count = db.query(OutgoingStockModel).count()
            out_amount = db.query(func.sum(OutgoingStockModel.total_amount)).scalar() or 0
            out_discount = db.query(func.sum(OutgoingStockModel.discount_amount)).scalar() or 0

            # Fetch only the last 5 entries to save memory and load the page instantly
            recent_in = db.query(IncomingStockModel).order_by(IncomingStockModel.id.desc()).limit(5).all()
            recent_out = db.query(OutgoingStockModel).order_by(OutgoingStockModel.id.desc()).limit(5).all()

            return {
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


# ==============================================================================
# Incoming Stock (Purchases) Service
# ==============================================================================
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
        """Allows users to search by Product Name or Supplier instantly."""
        with SessionLocal() as db:
            query = f"%{term}%" # The % symbols tell SQL to match partial words
            rows = db.query(IncomingStockModel).filter(
                or_(IncomingStockModel.product_name.like(query), IncomingStockModel.source_name.like(query))
            ).order_by(IncomingStockModel.date_of_purchase.desc()).all()
            return [to_dict(r) for r in rows]

    @staticmethod
    def create(data: dict):
        """Creates a new purchase record and strictly calculates subtotal + taxes."""
        with SessionLocal() as db:
            # 1. Decode massive base64 strings to bytes to save DB space
            keys = ["product_photo", "bill_photo", "bilti_photo"]
            for k in keys:
                if k in data and data[k]:
                    data[k] = decode_photo(data[k])
            
            # 2. Never trust the frontend for math! Calculate the exact taxes and totals on the backend.
            qty = data.get("quantity", 0)
            price = data.get("price_per_unit", 0)
            tax_pct = data.get("tax_percent", 0)
            discount = data.get("discount_amount", 0)
            subtotal = (qty * price) - discount
            tax_amount = subtotal * (tax_pct / 100)
            data["tax_amount"] = tax_amount
            data["amount"] = subtotal + tax_amount
            
            # Save to Database
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

            # Handle photo fields very carefully so we never accidentally delete 
            # a previously uploaded photo just because the user didn't re-upload it.
            for k in ["product_photo", "bill_photo", "bilti_photo"]:
                if k in data:
                    if data[k] == "delete":
                        data[k] = None  # User explicitly clicked delete
                    elif data[k]:  
                        data[k] = base64.b64decode(data[k]) # User uploaded a fresh replacement
                    else:
                        data.pop(k)  # User ignored the field — keep existing photo untouched

            for k, v in data.items():
                setattr(stock, k, v)

            # Recalculate amounts
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

    # --- Payment Logic ---
    @staticmethod
    def get_payments(stock_id: int):
        with SessionLocal() as db:
            rows = db.query(PaymentTransactionModel).filter(PaymentTransactionModel.stock_id == stock_id).all()
            return [{"id": r.id, "amount": r.amount, "payment_date": r.payment_date, "payment_type": r.payment_type, "notes": r.notes} for r in rows]

    @staticmethod
    def add_payment(stock_id: int, data: dict):
        """Logs partial payments and updates the main invoice status automatically."""
        with SessionLocal() as db:
            stock = db.get(IncomingStockModel, stock_id)
            if not stock: return
            
            payment = PaymentTransactionModel(stock_id=stock_id, **data)
            db.add(payment)
            
            # Auto-calculate string status based on mathematics
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
                # Refund the amount mathematically
                stock.amount_paid = max(0, stock.amount_paid - amt)
                if stock.amount_paid >= stock.amount:
                    stock.payment_status = "paid"
                elif stock.amount_paid > 0:
                    stock.payment_status = "partial"
                else:
                    stock.payment_status = "pending"
            db.commit()
            return True


# ==============================================================================
# Outgoing Stock (Sales) Service
# ==============================================================================
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
            # Auto-generate a beautiful Invoice Number (e.g., INV-2026-0034)
            if not data.get("invoice_no"):
                year = datetime.now().year
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

            for k in ["product_photo", "bill_photo"]:
                if k in data:
                    if data[k] == "delete":
                        data[k] = None
                    elif data[k]:  
                        data[k] = base64.b64decode(data[k])
                    else:
                        data.pop(k)

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


# ==============================================================================
# Live Inventory (Aggregates logic)
# ==============================================================================
class LiveInventory:
    @staticmethod
    def get_all():
        from database.database import SessionLocal
        with SessionLocal() as db:
            """
            Why Raw SQL here instead of ORM?
            Live Inventory requires extremely complex calculations. We must mathematically subtract 
            everything Sold from everything Bought, and append Supplier names and Images. Writing
            this in Python ORM would be incredibly slow. Running raw SQL is 100x faster for Analytics.
            """
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

# ==============================================================================
# Artificial Intelligence API Integration
# ==============================================================================
def scan_bill_image(base64_image: str, suggested_type: str = "generic"):
    """
    Sends images of handwritten bills or invoices to Google's Gemini Vision AI to read
    the text and auto-fill our application forms.
    
    Why use pure 'requests.post'?: We could have installed the 'google-generativeai' completely 
    heavy Python library, but manually sending one REST API call keeps our project tiny, 
    makes debugging easier, and removes heavy bloat.
    
    Why Gemini over Tesseract/OCR?: Older barcode and text scanners like Tesseract are bad 
    at reading handwriting. Modern LLM Vision APIs like Gemini instantly understand messy formats 
    and output exactly the JSON format we request.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"success": False, "error": "GEMINI_API_KEY is not set in your .env file."}

    # Clean the string for the AI API
    if "," in base64_image:
        base64_image = base64_image.split(",")[1]

    # The magic prompt! We tell the AI exactly what JSON shape to output
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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    try:
        response = requests.post(url, json=request_body, timeout=30)
        response.raise_for_status()
    except Exception as e:
        return {"success": False, "error": f"Gemini API call failed: {str(e)}"}

    try:
        raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        # Sometimes AI adds backticks like ```json ... ```. We clean it out reliably.
        clean_text = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        extracted = json.loads(clean_text)
        extracted["success"] = True
        return extracted
    except Exception as e:
        return {"success": False, "error": f"Could not parse Gemini response: {str(e)}"}