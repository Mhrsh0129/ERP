"""
routers/dashboard.py — Dashboard stats and database debug routes.

These routes don't share a common prefix, so we leave prefix="" on the router
and write full paths in each decorator.
"""

import mysql.connector
from fastapi import APIRouter, HTTPException

from app.models.dashboard import Dashboard
from app.core.database import db_config, test_connection


router = APIRouter(tags=["Dashboard & Debug"])


# ── GET /api/dashboard ────────────────────────────────────────────────────────
# Returns summary stats for the main dashboard page
@router.get("/api/dashboard")
def get_dashboard():
    return {"success": True, "data": Dashboard.get_stats()}


# ── GET /api/test-connection ──────────────────────────────────────────────────
# Quick health check — visit this URL to confirm the DB is reachable
@router.get("/api/test-connection")
def test_db_connection():
    if not test_connection():
        raise HTTPException(status_code=500, detail="Database connection failed")
    return {"success": True, "message": "Database connected successfully"}


# ── GET /api/debug ────────────────────────────────────────────────────────────
# Opens a raw connection and returns which host was used.
# Useful for debugging which DB server the app is connecting to.
@router.get("/api/debug")
def debug_db():
    conn = mysql.connector.connect(**db_config)
    if not conn.is_connected():
        raise HTTPException(
            status_code=500, detail="Connection returned but is_connected() is False"
        )
    return {"status": "success", "message": "Connected!", "host": db_config.get("host")}
