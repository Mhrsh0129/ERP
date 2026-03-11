"""
schemas/stock.py — Pydantic models for request validation.

In FastAPI, when the frontend sends JSON data to an API route,
FastAPI automatically validates it against these "schema" classes.

- If a required field is missing → FastAPI returns a 422 error automatically
- If a field has the wrong type → FastAPI returns a 422 error automatically
- Optional[str] = None means "this field is optional, default is None (empty)"

These schemas define the SHAPE of the data we expect in POST/PUT requests.
"""

from pydantic import BaseModel  # BaseModel is the base class for all schemas
from typing import Optional  # Optional means the field can be None


# ── Incoming Stock ─────────────────────────────────────────────────────────────


class IncomingStockCreate(BaseModel):
    """
    Schema for creating a new incoming stock entry.
    Used in: POST /api/incoming-stock
    """

    product_name: str  # Required — must always be provided
    source_name: Optional[str] = None  # Optional — supplier name
    date_of_purchase: Optional[str] = None  # Optional — format: "YYYY-MM-DD"
    quantity: Optional[float] = 1.0
    unit: Optional[str] = "pcs"  # e.g. kg, bags, pcs
    price_per_unit: Optional[float] = 0.0
    tax_percent: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    payment_status: Optional[str] = "pending"  # pending / partial / paid
    amount_paid: Optional[float] = 0.0
    payment_type: Optional[str] = None  # cash / cheque / UPI etc.
    payment_date: Optional[str] = None
    delivery_date: Optional[str] = None
    product_photo: Optional[str] = None  # Base64-encoded image string
    bill_photo: Optional[str] = None  # Base64-encoded image string
    bilti_photo: Optional[str] = None  # Base64-encoded image string


class IncomingStockUpdate(IncomingStockCreate):
    """
    Schema for updating an existing incoming stock entry.
    Used in: PUT /api/incoming-stock/{id}

    It inherits all fields from IncomingStockCreate — same fields, same rules.
    """

    pass  # "pass" means "no changes, just inherit everything from parent"


# ── Payment ────────────────────────────────────────────────────────────────────


class PaymentCreate(BaseModel):
    """
    Schema for adding a payment instalment.
    Used in: POST /api/incoming-stock/{id}/payments
             POST /api/outgoing-stock/{id}/payments
    """

    amount: float  # Required
    payment_date: str  # Required — format: "YYYY-MM-DD"
    payment_type: str  # Required — cash / cheque / UPI etc.
    notes: Optional[str] = None


# ── Outgoing Stock ─────────────────────────────────────────────────────────────


class OutgoingStockCreate(BaseModel):
    """
    Schema for creating a new outgoing stock (sale) entry.
    Used in: POST /api/outgoing-stock
    """

    invoice_no: Optional[str] = None  # Auto-generated if not provided
    product_name: str  # Required
    customer_name: Optional[str] = None
    gst_number: Optional[str] = ""
    date_of_sale: Optional[str] = None
    quantity: Optional[float] = 1.0
    unit: Optional[str] = "pcs"
    price_per_unit: Optional[float] = 0.0
    total_amount: float  # Required — total bill amount
    tax: Optional[float] = 0.0  # Tax amount (in rupees)
    tax_percentage: Optional[float] = 5.0  # Tax rate (in percent)
    discount_amount: Optional[float] = 0.0
    payment_type: Optional[str] = None
    payment_date: Optional[str] = None
    delivery_date: Optional[str] = None
    bill_photo: Optional[str] = None  # Base64-encoded image
    product_photo: Optional[str] = None  # Base64-encoded image


class OutgoingStockUpdate(OutgoingStockCreate):
    """
    Schema for updating an existing sale entry.
    Used in: PUT /api/outgoing-stock/{id}
    """

    pass  # Same fields as OutgoingStockCreate


# ── Product Details ────────────────────────────────────────────────────────────


class ProductDetailsUpdate(BaseModel):
    """
    Schema for adding/updating extra notes for a product in inventory.
    Used in: POST /api/inventory/details
    """

    product_name: str  # Which product to update
    details: str  # The new notes/description text


# ── AI Scan ────────────────────────────────────────────────────────────────────


class ScanBillRequest(BaseModel):
    """
    Schema for the AI bill scanner endpoint.
    Used in: POST /api/scan-bill
    """

    image: str  # Base64-encoded image of the bill
    suggested_type: Optional[str] = None  # Hint: "incoming" or "outgoing"
