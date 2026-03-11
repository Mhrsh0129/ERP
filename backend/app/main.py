"""
main.py — The entry point of the FastAPI application.

This is the first file FastAPI reads. It:
  1. Creates the app object
  2. Adds CORS middleware (so the frontend HTML can call the API)
  3. Runs DB setup when the server starts
  4. Registers all the routers (groups of related routes)
  5. Serves the frontend HTML files
"""

import os

# FastAPI is the main web framework
from fastapi import FastAPI, HTTPException

# CORSMiddleware allows browsers to make requests to this API
# (Without it, the browser blocks requests from HTML files to localhost)
from fastapi.middleware.cors import CORSMiddleware

# FileResponse is used to send HTML/CSS/JS files to the browser
from fastapi.responses import FileResponse

# These are our database helper functions
from app.core.database import init_connection_pool, init_db_schema

# These are our route groups — each file handles one section of the API
from app.routers.incoming import router as incoming_router, payments_router
from app.routers.outgoing import router as outgoing_router, sales_payments_router
from app.routers.inventory import router as inventory_router
from app.routers.dashboard import router as dashboard_router
from app.routers.scan import router as scan_router


# ── Create the app ────────────────────────────────────────────────────────────
# FastAPI() creates the application. title and description show up in /docs
app = FastAPI(
    title="Jay Shree Traders ERP API",
    description="Inventory management system for Jay Shree Traders.",
    version="2.0.0",
)


# ── CORS Middleware ───────────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# Our frontend HTML files run from a different "origin" than the API,
# so we need this or the browser will reject the API calls.
# allow_origins=["*"] means "allow requests from any website or file"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)


# ── Startup event ─────────────────────────────────────────────────────────────
# @app.on_event("startup") runs this function once when the server starts.
# We use it to set up the database before any requests come in.
@app.on_event("startup")
def startup():
    print("🚀 Starting Jay Shree Traders ERP...")
    init_connection_pool()
    init_db_schema()


# ── Register Routers ──────────────────────────────────────────────────────────
# include_router() adds a group of routes to the app.
# Instead of putting all 20+ routes in this one file, we split them into
# separate router files for better organisation.
app.include_router(dashboard_router)  # /api/dashboard, /api/debug
app.include_router(incoming_router)  # /api/incoming-stock
app.include_router(payments_router)  # /api/payments
app.include_router(outgoing_router)  # /api/outgoing-stock
app.include_router(sales_payments_router)  # /api/sales-payments
app.include_router(inventory_router)  # /api/inventory
app.include_router(scan_router)  # /api/scan-bill


# ── Serve Frontend HTML Files ─────────────────────────────────────────────────
# Build the path to the frontend/ folder (two levels above this file)
frontend_dir = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")
)


# This catch-all route handles any URL that wasn't matched by the API routes above.
# {full_path:path} means "match anything"
@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    # Try to find and return the exact file the browser is asking for
    file_path = os.path.join(frontend_dir, full_path)
    if full_path and os.path.isfile(file_path):
        # service-worker.js needs Cache-Control: no-cache so the browser always gets latest
        if "service-worker" in os.path.basename(file_path) and file_path.endswith(
            ".js"
        ):
            return FileResponse(
                file_path,
                media_type="application/javascript",
                headers={"Cache-Control": "no-cache"},
            )
        return FileResponse(file_path)

    # Fall back to index.html for direct page navigation
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Not Found")
