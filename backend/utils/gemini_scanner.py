"""
Gemini AI Bill Scanner Utility
Uses Google Gemini 1.5 Flash REST API for OCR and data extraction from bills/invoices.
Replaces the google-generativeai library to avoid Protobuf compatibility issues.
"""

import requests
import os
import base64
from PIL import Image
import io
import json
from typing import Dict, Optional


class GeminiBillScanner:
    """
    AI-powered bill scanning using Google Gemini Vision REST API.
    Extracts structured data from handwritten or printed bills.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from environment or parameter."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={self.api_key}"

    def scan_bill(self, image_data: str, suggested_type: str = None) -> Dict:
        """
        Scan bill image and extract structured data using REST API.

        Args:
            image_data: Base64 encoded image string
            suggested_type: Optional hint - 'incoming' or 'outgoing'

        Returns:
            Dictionary with extracted bill data
        """
        import time

        max_retries = 3
        retry_delay = 1

        try:
            # Decode base64 image
            image_bytes = base64.b64decode(
                image_data.split(",")[-1] if "," in image_data else image_data
            )
            image = Image.open(io.BytesIO(image_bytes))

            # Optimize image if too large
            if image.width > 2048 or image.height > 2048:
                image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)

            # Save optimized image to bytes
            img_byte_arr = io.BytesIO()
            # Default to PNG if format is not available
            image_format = image.format if image.format else "PNG"
            image.save(img_byte_arr, format=image_format)
            img_bytes = img_byte_arr.getvalue()

            # Encode back to base64 for API
            b64_image = base64.b64encode(img_bytes).decode("utf-8")

            # Create extraction prompt
            prompt_text = self._create_extraction_prompt(suggested_type)

            # Construct Payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt_text},
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

            # Send Request with Retry Logic
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        self.api_url,
                        headers={"Content-Type": "application/json"},
                        json=payload,
                        timeout=30,
                    )

                    response.raise_for_status()
                    break  # Success, exit retry loop

                except requests.exceptions.HTTPError as e:
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            raise e  # Max retries reached
                    else:
                        raise e  # Other HTTP error

            response_json = response.json()

            # Parse response
            # Extract text from response structure
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
                "message": "Failed to process bill image (REST)",
                "details": error_details,
            }

    def _parse_response(self, response_text: str) -> Dict:
        """Parse Gemini response and extract JSON."""
        try:
            # Remove markdown code blocks if present
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                # Extract JSON from code block
                parts = clean_text.split("```")
                if len(parts) > 1:
                    clean_text = parts[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
                clean_text = clean_text.strip()

            # Parse JSON
            data = json.loads(clean_text)

            # Post-process and clean data
            data = self._clean_extracted_data(data)

            # Validate and set defaults
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
            # Fallback: try to extract data manually
            return {
                "bill_type": "incoming",
                "data": {},
                "confidence": 0.0,
                "raw_response": response_text,
                "parse_error": str(e),
            }

    def _clean_extracted_data(self, data: Dict) -> Dict:
        """Post-process extracted data to fix common OCR/AI errors."""
        import re

        # Helper to clean numbers
        def clean_number(value):
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return value

            s_val = str(value).strip()
            # Remove spaces (common AI error: "12 500" -> "12500")
            s_val = s_val.replace(" ", "")
            # Remove commas (std format: "1,200" -> "1200")
            s_val = s_val.replace(",", "")
            # Remove currency symbols if any slipped through
            s_val = re.sub(r"[^\d.]", "", s_val)

            try:
                return float(s_val)
            except ValueError:
                return None

        # Clean numeric fields
        numeric_fields = [
            "quantity",
            "price_per_unit",
            "tax_percentage",
            "tax_percentage",
            "total_amount",
            "discount_amount",
        ]
        for field in numeric_fields:
            if field in data:
                data[field] = clean_number(data[field])

        # Basic Sanity Check: if Total is huge but Qty * Price is small -> likely decimal error
        # Example: Qty 10, Price 50, Total 50000 (AI read "500.00" as "50000")
        try:
            qty = data.get("quantity") or 0
            price = data.get("price_per_unit") or 0
            total = data.get("total_amount") or 0

            if qty > 0 and price > 0 and total > 0:
                calc_total = qty * price
                # If calculated total is roughly 1/100th of extracted total, divide extracted by 100
                if 90 < (total / calc_total) < 110:
                    # Matches well, do nothing
                    pass
                elif 90 < (total / (calc_total * 100)) < 110:
                    # Extracted is ~100x larger -> divide by 100
                    data["total_amount"] = total / 100
        except Exception:
            pass

        return data

    def _create_extraction_prompt(self, suggested_type: Optional[str]) -> str:
        """Create optimized prompt for Gemini API."""

        type_hint = ""
        if suggested_type:
            type_hint = f"\nHINT: This is likely a {suggested_type} stock bill."

        prompt = f"""You are an expert Indian invoice/bill data extraction assistant.

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
9. GST number (if visible)
10. Invoice/Bill number
11. Discount Amount (numerical value only)

CRITICAL FORMATTING RULES (STRICT):
1. NUMBERS: Output purely as digits (e.g., 1500.50). NEVER use spaces inside a number (e.g., "1 500" is INVALID, use "1500").
2. DECIMALS: Always use a period (.) for decimals.
3. COMMAS: Do NOT use commas for thousands (e.g., use 12500, NOT 12,500).
4. AMBIGUOUS SPACES: If you see "10 00", check context. If it aligns with a price of 1000, output 1000. If it aligns with 10.00, output 10.00.
5. JSON ONLY: Do not output any markdown or explanation, just the JSON.

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

        return prompt


# Convenience function for Flask route
def scan_bill_image(image_data: str, suggested_type: str = None) -> Dict:
    """
    Scan bill and return extracted data.
    Convenience wrapper for Flask routes.
    """
    scanner = GeminiBillScanner()
    return scanner.scan_bill(image_data, suggested_type)
