"""
main.py — The single entry point of the FastAPI application.
"""

import os
import traceback
from dotenv import load_dotenv

# Load .env so GEMINI_API_KEY and other variables are available via os.getenv()
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from database.database import engine, Base

# Import business logic
from services.services import (
    Dashboard,
    IncomingStock,
    OutgoingStock,
    LiveInventory,
    scan_bill_image
)

# Import schemas AND Models to register them
from model.model import (
    IncomingStockModel, OutgoingStockModel, PaymentTransactionModel, SalesPaymentModel, ProductDetailModel,
    IncomingStockCreate, IncomingStockUpdate, PaymentCreate,
    OutgoingStockCreate, OutgoingStockUpdate, ProductDetailsUpdate, ScanBillRequest
)

app = FastAPI(title="ERP API", version="2.0.0")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    err_msg = traceback.format_exc()
    print(f"Unhandled Exception: {err_msg}")
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

@app.on_event("startup")
def startup():
    try:
        # Create all tables explicitly using SQLAlchemy
        Base.metadata.create_all(bind=engine)
        
        # We must create the live_inventory VIEW manually since SQLAlchemy create_all does not manage views
        with engine.begin() as conn:
            from sqlalchemy import text
            # DROP first so the fixed version always takes effect on restart
            conn.execute(text("DROP VIEW IF EXISTS live_inventory"))
            conn.execute(text("""
                CREATE VIEW live_inventory AS
                SELECT
                    MAX(product_name) AS product_name,
                    SUM(qty)          AS current_stock,
                    MAX(unit)         AS unit
                FROM (
                    SELECT product_name, quantity AS qty, unit FROM incoming_stock
                    UNION ALL
                    SELECT product_name, -quantity AS qty, unit FROM outgoing_stock
                )
                GROUP BY lower(product_name)
            """))

        print("✅ Database connected and tables/views created.")
    except Exception as e:
        print(f"DB Warning: {e}")


# ────────────────────────────────────────────────────────────────────────────────
# Dashboard Routes
# ────────────────────────────────────────────────────────────────────────────────

@app.get("/api/dashboard")
def get_dashboard():
    return {"success": True, "data": Dashboard.get_stats()}

@app.get("/api/test-connection")
def test_db_connection():
    try:
        with engine.connect() as conn:
            pass
        return {"success": True, "message": "Database connected successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/api/debug")
def debug_db():
    return {"status": "success", "message": "Connected to SQLite!"}


# ────────────────────────────────────────────────────────────────────────────────
# Incoming Stock Routes
# ────────────────────────────────────────────────────────────────────────────────

@app.get("/api/incoming-stock")
def get_incoming_stock(search: str = ""):
    data = IncomingStock.search(search) if search else IncomingStock.get_all()
    return {"success": True, "data": data}

@app.get("/api/incoming-stock/{stock_id}")
def get_incoming_stock_by_id(stock_id: int):
    row = IncomingStock.get_by_id(stock_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {"success": True, "data": row}

@app.post("/api/incoming-stock", status_code=201)
def create_incoming_stock(data: IncomingStockCreate):
    new_id = IncomingStock.create(data.model_dump(exclude_unset=True))
    return {"success": True, "id": new_id, "message": "Stock added successfully"}

@app.put("/api/incoming-stock/{stock_id}")
def update_incoming_stock(stock_id: int, data: IncomingStockUpdate):
    IncomingStock.update(stock_id, data.model_dump(exclude_unset=True))
    return {"success": True, "message": "Stock updated successfully"}

@app.delete("/api/incoming-stock/{stock_id}")
def delete_incoming_stock(stock_id: int):
    IncomingStock.delete(stock_id)
    return {"success": True, "message": "Stock deleted successfully"}

@app.get("/api/incoming-stock/{stock_id}/payments")
def get_stock_payments(stock_id: int):
    return {"success": True, "data": IncomingStock.get_payments(stock_id)}

@app.post("/api/incoming-stock/{stock_id}/payments", status_code=201)
def add_stock_payment(stock_id: int, data: PaymentCreate):
    IncomingStock.add_payment(stock_id, data.model_dump(exclude_unset=True))
    return {"success": True}

@app.delete("/api/payments/{payment_id}")
def delete_payment(payment_id: int):
    result = IncomingStock.delete_payment(payment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"success": True}


# ────────────────────────────────────────────────────────────────────────────────
# Outgoing Stock Routes
# ────────────────────────────────────────────────────────────────────────────────

@app.get("/api/outgoing-stock")
def get_outgoing_stock(search: str = ""):
    data = OutgoingStock.search(search) if search else OutgoingStock.get_all()
    return {"success": True, "data": data}

@app.get("/api/outgoing-stock/{stock_id}")
def get_outgoing_stock_by_id(stock_id: int):
    row = OutgoingStock.get_by_id(stock_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {"success": True, "data": row}

@app.post("/api/outgoing-stock", status_code=201)
def create_outgoing_stock(data: OutgoingStockCreate):
    new_id = OutgoingStock.create(data.model_dump(exclude_unset=True))
    return {"success": True, "id": new_id, "message": "Sale added successfully"}

@app.put("/api/outgoing-stock/{stock_id}")
def update_outgoing_stock(stock_id: int, data: OutgoingStockUpdate):
    OutgoingStock.update(stock_id, data.model_dump(exclude_unset=True))
    return {"success": True, "message": "Sale updated successfully"}

@app.delete("/api/outgoing-stock/{stock_id}")
def delete_outgoing_stock(stock_id: int):
    OutgoingStock.delete(stock_id)
    return {"success": True, "message": "Stock deleted successfully"}

@app.get("/api/outgoing-stock/{stock_id}/payments")
def get_sales_payments(stock_id: int):
    return {"success": True, "data": OutgoingStock.get_payments(stock_id)}

@app.post("/api/outgoing-stock/{stock_id}/payments", status_code=201)
def add_sales_payment(stock_id: int, data: PaymentCreate):
    OutgoingStock.add_payment(stock_id, data.model_dump(exclude_unset=True))
    return {"success": True}

@app.delete("/api/sales-payments/{payment_id}")
def delete_sales_payment(payment_id: int):
    result = OutgoingStock.delete_payment(payment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"success": True}


# ────────────────────────────────────────────────────────────────────────────────
# Inventory Routes
# ────────────────────────────────────────────────────────────────────────────────

@app.get("/api/inventory")
def get_inventory():
    return {"success": True, "data": LiveInventory.get_all()}

@app.get("/api/inventory/low-stock")
def get_low_stock():
    return {"success": True, "data": LiveInventory.get_low_stock()}

@app.post("/api/inventory/details")
def update_product_details(data: ProductDetailsUpdate):
    LiveInventory.update_details(data.product_name, data.details)
    return {"success": True, "message": "Details updated successfully"}


# ────────────────────────────────────────────────────────────────────────────────
# Scan Bill Routes
# ────────────────────────────────────────────────────────────────────────────────

@app.post("/api/scan-bill")
def scan_bill(data: ScanBillRequest):
    result = scan_bill_image(data.image, data.suggested_type)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Scan failed"))
    return result


# ────────────────────────────────────────────────────────────────────────────────
# Serve Frontend
# ────────────────────────────────────────────────────────────────────────────────

frontend_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend"))

@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    file_path = os.path.join(frontend_dir, full_path)
    if full_path and os.path.isfile(file_path):
        if "service-worker" in os.path.basename(file_path) and file_path.endswith(".js"):
            return FileResponse(file_path, media_type="application/javascript", headers={"Cache-Control": "no-cache"})
        return FileResponse(file_path)
    
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
        
    raise HTTPException(status_code=404, detail="Not Found")
