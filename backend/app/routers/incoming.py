"""
routers/incoming.py — All routes related to Incoming Stock.

In FastAPI, an APIRouter is like a mini-app that holds a group of routes.
We use routers to keep the code organised — instead of putting every route
in main.py, we split them by topic.

prefix="/api/incoming-stock" means every route here starts with that path.
tags=["Incoming Stock"] groups them together in the /docs page.
"""

from fastapi import APIRouter, HTTPException

# Import the model class that handles DB operations for incoming stock
from app.models.incoming_stock import IncomingStock

# Import the schema classes that validate the request body data
from app.schemas.stock import IncomingStockCreate, IncomingStockUpdate, PaymentCreate


router = APIRouter(prefix="/api/incoming-stock", tags=["Incoming Stock"])


# ── GET /api/incoming-stock ────────────────────────────────────────────────────
# Returns all stock entries. ?search=xyz filters by product/source name.
@router.get("")
def get_incoming_stock(search: str = ""):
    # If search text is provided, call search(); otherwise get everything
    data = IncomingStock.search(search) if search else IncomingStock.get_all()
    return {"success": True, "data": data}


# ── GET /api/incoming-stock/{stock_id} ────────────────────────────────────────
# {stock_id} is a path parameter — its value comes from the URL
@router.get("/{stock_id}")
def get_incoming_stock_by_id(stock_id: int):
    row = IncomingStock.get_by_id(stock_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {"success": True, "data": row}


# ── POST /api/incoming-stock ───────────────────────────────────────────────────
# Creates a new stock entry. status_code=201 means "Created" (standard for POST).
# FastAPI automatically validates `data` against IncomingStockCreate schema.
@router.post("", status_code=201)
def create_incoming_stock(data: IncomingStockCreate):
    # model_dump() converts the Pydantic object to a plain Python dict
    # exclude_unset=True skips fields not sent in the request (keeps DB defaults)
    new_id = IncomingStock.create(data.model_dump(exclude_unset=True))
    return {"success": True, "id": new_id, "message": "Stock added successfully"}


# ── PUT /api/incoming-stock/{stock_id} ────────────────────────────────────────
# Updates an existing entry. PUT replaces the full record.
@router.put("/{stock_id}")
def update_incoming_stock(stock_id: int, data: IncomingStockUpdate):
    IncomingStock.update(stock_id, data.model_dump(exclude_unset=True))
    return {"success": True, "message": "Stock updated successfully"}


# ── DELETE /api/incoming-stock/{stock_id} ─────────────────────────────────────
@router.delete("/{stock_id}")
def delete_incoming_stock(stock_id: int):
    IncomingStock.delete(stock_id)
    return {"success": True, "message": "Stock deleted successfully"}


# ── GET /api/incoming-stock/{stock_id}/payments ───────────────────────────────
@router.get("/{stock_id}/payments")
def get_stock_payments(stock_id: int):
    return {"success": True, "data": IncomingStock.get_payments(stock_id)}


# ── POST /api/incoming-stock/{stock_id}/payments ──────────────────────────────
@router.post("/{stock_id}/payments", status_code=201)
def add_stock_payment(stock_id: int, data: PaymentCreate):
    IncomingStock.add_payment(stock_id, data.model_dump(exclude_unset=True))
    return {"success": True}


# ── DELETE /api/payments/{payment_id} ─────────────────────────────────────────
# This endpoint has a different prefix (/api/payments) so we define it as a
# separate router and register it independently in main.py.
payments_router = APIRouter(prefix="/api/payments", tags=["Incoming Payments"])


@payments_router.delete("/{payment_id}")
def delete_payment(payment_id: int):
    result = IncomingStock.delete_payment(payment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"success": True}
