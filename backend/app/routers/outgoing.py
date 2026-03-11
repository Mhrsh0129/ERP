"""
routers/outgoing.py — All routes related to Outgoing Stock (Sales).

Same structure as incoming.py — uses APIRouter with prefix="/api/outgoing-stock".
"""

from fastapi import APIRouter, HTTPException

from app.models.outgoing_stock import OutgoingStock
from app.schemas.stock import OutgoingStockCreate, OutgoingStockUpdate, PaymentCreate


router = APIRouter(prefix="/api/outgoing-stock", tags=["Outgoing Stock"])


@router.get("")
def get_outgoing_stock(search: str = ""):
    data = OutgoingStock.search(search) if search else OutgoingStock.get_all()
    return {"success": True, "data": data}


@router.get("/{stock_id}")
def get_outgoing_stock_by_id(stock_id: int):
    row = OutgoingStock.get_by_id(stock_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {"success": True, "data": row}


@router.post("", status_code=201)
def create_outgoing_stock(data: OutgoingStockCreate):
    new_id = OutgoingStock.create(data.model_dump(exclude_unset=True))
    return {"success": True, "id": new_id, "message": "Sale added successfully"}


@router.put("/{stock_id}")
def update_outgoing_stock(stock_id: int, data: OutgoingStockUpdate):
    OutgoingStock.update(stock_id, data.model_dump(exclude_unset=True))
    return {"success": True, "message": "Sale updated successfully"}


@router.delete("/{stock_id}")
def delete_outgoing_stock(stock_id: int):
    OutgoingStock.delete(stock_id)
    return {"success": True, "message": "Stock deleted successfully"}


@router.get("/{stock_id}/payments")
def get_sales_payments(stock_id: int):
    return {"success": True, "data": OutgoingStock.get_payments(stock_id)}


@router.post("/{stock_id}/payments", status_code=201)
def add_sales_payment(stock_id: int, data: PaymentCreate):
    OutgoingStock.add_payment(stock_id, data.model_dump(exclude_unset=True))
    return {"success": True}


# ── DELETE /api/sales-payments/{payment_id} ───────────────────────────────────
# Separate prefix — registered independently in main.py
sales_payments_router = APIRouter(prefix="/api/sales-payments", tags=["Sales Payments"])


@sales_payments_router.delete("/{payment_id}")
def delete_sales_payment(payment_id: int):
    result = OutgoingStock.delete_payment(payment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"success": True}
