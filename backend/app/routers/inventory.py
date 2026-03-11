"""
routers/inventory.py — Routes for the Live Inventory view.

Live inventory is calculated (incoming - outgoing), so it's read-only.
"""

from fastapi import APIRouter

from app.models.inventory import LiveInventory
from app.schemas.stock import ProductDetailsUpdate


router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


# ── GET /api/inventory ────────────────────────────────────────────────────────
# Returns current stock level for every product
@router.get("")
def get_inventory():
    return {"success": True, "data": LiveInventory.get_all()}


# ── GET /api/inventory/low-stock ──────────────────────────────────────────────
# Returns products running low (currently returns empty — no reorder level yet)
@router.get("/low-stock")
def get_low_stock():
    return {"success": True, "data": LiveInventory.get_low_stock()}


# ── POST /api/inventory/details ───────────────────────────────────────────────
# Saves extra notes for a product (brand, specs, storage info, etc.)
@router.post("/details")
def update_product_details(data: ProductDetailsUpdate):
    LiveInventory.update_details(data.product_name, data.details)
    return {"success": True, "message": "Details updated successfully"}
