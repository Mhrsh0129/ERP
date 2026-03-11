"""
routers/scan.py — AI Bill Scanner route.

Sends a bill photo to Gemini AI and returns the extracted data as JSON.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.stock import ScanBillRequest


router = APIRouter(prefix="/api", tags=["AI Scan"])


# ── POST /api/scan-bill ───────────────────────────────────────────────────────
# Receives a bill image (base64 string) and returns extracted fields like
# product name, amount, date, etc.
@router.post("/scan-bill")
def scan_bill(data: ScanBillRequest):
    # Lazy import — so the app starts even if GEMINI_API_KEY is not set.
    # The error only appears if someone actually calls this endpoint.
    from app.utils.gemini_scanner import scan_bill_image

    result = scan_bill_image(data.image, data.suggested_type)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Scan failed"))
    return result
