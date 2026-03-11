"""
Gemini AI Bill Scanner Utility
Uses Google Gemini Flash REST API for OCR and data extraction from bills/invoices.
"""

import requests
import os
import base64
import json
import io
import re
import time
from typing import Dict, Optional

from PIL import Image


class GeminiBillScanner:
    """AI-powered bill scanning using Google Gemini Vision REST API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        self.api_url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-flash-latest:generateContent?key={self.api_key}"
        )

    def scan_bill(self, image_data: str, suggested_type: Optional[str] = None) -> Dict:
        max_retries = 3
        retry_delay = 1

        try:
            raw = image_data.split(",")[-1] if "," in image_data else image_data
            image_bytes = base64.b64decode(raw)
            image = Image.open(io.BytesIO(image_bytes))

            if image.width > 2048 or image.height > 2048:
                image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            image_format = image.format or "PNG"
            image.save(buf, format=image_format)
            b64_image = base64.b64encode(buf.getvalue()).decode("utf-8")

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": self._create_extraction_prompt(suggested_type)},
                            {
                                "inline_data": {
                                    "mime_type": f"image/{image_format.lower()}",
                                    "data": b64_image,
                                }
                            },
                        ]
                    }
                ],
                "generationConfig": {"response_mime_type": "application/json"},
            }

            response = None
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        self.api_url,
                        headers={"Content-Type": "application/json"},
                        json=payload,
                        timeout=30,
                    )
                    response.raise_for_status()
                    break
                except requests.exceptions.HTTPError:
                    if (
                        response is not None
                        and response.status_code == 429
                        and attempt < max_retries - 1
                    ):
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    raise

            response_json = response.json()
            try:
                text_result = response_json["candidates"][0]["content"]["parts"][0][
                    "text"
                ]
                result = self._parse_response(text_result)
                return {"success": True, **result}
            except (KeyError, IndexError):
                return {
                    "success": False,
                    "error": "Invalid API response structure",
                    "details": str(response_json),
                }

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"ERROR in scan_bill: {error_details}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process bill image",
                "details": error_details,
            }

    def _parse_response(self, response_text: str) -> Dict:
        try:
            clean = response_text.strip()
            if clean.startswith("```"):
                parts = clean.split("```")
                if len(parts) > 1:
                    clean = parts[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip()

            data = json.loads(clean)
            data = self._clean_extracted_data(data)

            return {
                "bill_type": data.get("bill_type", "incoming"),
                "data": {
                    "product_name": data.get("product_name"),
                    "supplier_name": data.get("supplier_name")
                    if data.get("bill_type") == "incoming"
                    else None,
                    "customer_name": data.get("customer_name")
                    if data.get("bill_type") == "outgoing"
                    else None,
                    "date": data.get("date"),
                    "quantity": data.get("quantity"),
                    "unit": data.get("unit"),
                    "price_per_unit": data.get("price_per_unit"),
                    "tax_percentage": data.get("tax_percentage"),
                    "total_amount": data.get("total_amount"),
                    "gst_number": data.get("gst_number"),
                    "invoice_number": data.get("invoice_number"),
                    "discount_amount": data.get("discount_amount"),
                },
                "confidence": data.get("confidence", 0.8),
                "raw_response": response_text,
            }
        except json.JSONDecodeError as e:
            return {
                "bill_type": "incoming",
                "data": {},
                "confidence": 0.0,
                "raw_response": response_text,
                "parse_error": str(e),
            }

    def _clean_extracted_data(self, data: Dict) -> Dict:
        def clean_number(value):
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return value
            s = str(value).strip().replace(" ", "").replace(",", "")
            s = re.sub(r"[^\d.]", "", s)
            try:
                return float(s)
            except ValueError:
                return None

        for field in [
            "quantity",
            "price_per_unit",
            "tax_percentage",
            "total_amount",
            "discount_amount",
        ]:
            if field in data:
                data[field] = clean_number(data[field])

        try:
            qty = data.get("quantity") or 0
            price = data.get("price_per_unit") or 0
            total = data.get("total_amount") or 0
            if qty > 0 and price > 0 and total > 0:
                calc_total = qty * price
                if 90 < (total / (calc_total * 100)) < 110:
                    data["total_amount"] = total / 100
        except Exception:
            pass

        return data

    def _create_extraction_prompt(self, suggested_type: Optional[str]) -> str:
        type_hint = (
            f"\nHINT: This is likely a {suggested_type} stock bill."
            if suggested_type
            else ""
        )

        return f"""You are an expert Indian invoice/bill data extraction assistant.

TASK: Analyze this bill/invoice image and extract structured data.

CLASSIFICATION:
Determine if this is "incoming" (purchase from supplier) or "outgoing" (sale to customer).
CRITICAL CONTEXT:
- My Company Name: "JAY SHREE TRADERS"
- My Role: I am the owner of this ERP system.

RULES FOR CLASSIFICATION:
1. OUTGOING (Sale): If "JAY SHREE TRADERS" is the SELLER (top header, logo, or "From" section) -> It is OUTGOING.
2. INCOMING (Purchase): If "JAY SHREE TRADERS" is the BUYER (in "Bill To", "Ship To", or "Consignee" section) -> It is INCOMING.
3. GENERAL Indicators:
   - INCOMING keywords: "Bought From", "Supplier", "Vendor".
   - OUTGOING keywords: "Sold To", "Customer", "Consignee".
{type_hint}

EXTRACT THE FOLLOWING DATA:
1. Product/Item name (if multiple items, focus on main item or combine)
2. Supplier/Customer name
3. Date in YYYY-MM-DD format
4. Quantity (numerical value only)
5. Unit (kg, bags, pieces, liters, etc.)
6. Price per unit (numerical value only)
7. GST/Tax percentage (numerical value only, e.g., 18)
8. Total amount (numerical value only)
9. GST number (if visible)
10. Invoice/Bill number
11. Discount Amount (numerical value only)

CRITICAL FORMATTING RULES (STRICT):
1. NUMBERS: Output purely as digits (e.g., 1500.50). NEVER use spaces inside a number.
2. DECIMALS: Always use a period (.) for decimals.
3. COMMAS: Do NOT use commas for thousands (use 12500, NOT 12,500).
4. JSON ONLY: Do not output any markdown or explanation, just the JSON.

Return ONLY a valid JSON object in this exact format.
{{
  "bill_type": "incoming" or "outgoing",
  "product_name": "extracted product name",
  "supplier_name": "extracted supplier/customer name",
  "customer_name": "extracted customer name (for outgoing)",
  "date": "YYYY-MM-DD",
  "quantity": number or null,
  "unit": "unit text" or null,
  "price_per_unit": number or null,
  "tax_percentage": number or null,
  "total_amount": number or null,
  "gst_number": "GST number" or null,
  "invoice_number": "invoice number" or null,
  "discount_amount": number or null,
  "confidence": 0.0 to 1.0
}}"""


def scan_bill_image(image_data: str, suggested_type: Optional[str] = None) -> Dict:
    """Convenience wrapper for router."""
    scanner = GeminiBillScanner()
    return scanner.scan_bill(image_data, suggested_type)
