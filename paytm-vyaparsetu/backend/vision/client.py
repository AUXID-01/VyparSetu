import base64
import json
import re
import httpx
from typing import Dict, Any
from config import settings
from core.errors import AppException, ErrorCode
from core.logging import get_logger
from .prompts import VISION_CHALLAN_EXTRACTION_PROMPT

logger = get_logger("vision.client")

def normalize_sku(sku: str) -> str:
    """
    Normalizes SKU casing and spacing.
    Example: '  dahi 200g  pouch ' -> 'Dahi 200g Pouch'
    """
    clean = re.sub(r'\s+', ' ', str(sku).strip())
    return clean.title() if clean else "Unknown Item"

def parse_ocr_text_to_challan_json(ocr_text: str) -> Dict[str, Any]:
    """
    Parses raw OCR text extracted from Google Cloud Vision into structured Kirana Challan JSON.
    """
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    
    # 1. Distributor guess (first line or line containing distributor keywords)
    distributor_guess = "Supplier / Distributor"
    for line in lines[:5]:
        if any(kw in line.lower() for kw in ["traders", "agency", "distributor", "enterprises", "dairy", "store", "ltd", "pvt", "amul", "mother", "dairy"]):
            distributor_guess = line
            break
    if distributor_guess == "Supplier / Distributor" and lines:
        distributor_guess = lines[0]

    # 2. Extract line items (matching item patterns: item name, qty, price)
    line_items = []
    total_amount = 0.0

    for line in lines:
        # Match lines like "Dahi 200g 50 x 28.50" or "Milk 1L 30 54.00" or "Dahi 50 28.5"
        nums = re.findall(r'\b\d+(?:\.\d+)?\b', line)
        words = re.findall(r'[a-zA-Z\u0900-\u097F]+', line)
        
        if len(nums) >= 2 and words:
            sku_name = normalize_sku(" ".join(words[:4]))
            try:
                qty = int(float(nums[0]))
                price = float(nums[1])
                if qty > 0 and price > 0:
                    item_total = qty * price
                    total_amount += item_total
                    line_items.append({
                        "sku": sku_name,
                        "quantity": qty,
                        "unit_price": price
                    })
            except Exception:
                continue

    # 3. Look for explicit total in lines
    for line in reversed(lines):
        if any(kw in line.lower() for kw in ["total", "net amount", "grand total", "g.total", "amount"]):
            found_nums = re.findall(r'\b\d+(?:\.\d+)?\b', line)
            if found_nums:
                try:
                    explicit_total = float(found_nums[-1])
                    if explicit_total > 0:
                        total_amount = explicit_total
                        break
                except Exception:
                    pass

    confidence = 0.85 if line_items else 0.50

    return {
        "distributor_name_guess": distributor_guess,
        "line_items": line_items,
        "total_amount": round(total_amount, 2),
        "extraction_confidence": confidence
    }

def extract_challan(image_bytes: bytes, request_id: str = "N/A") -> Dict[str, Any]:
    """
    Sends image bytes to Google Vision API (Cloud Vision OCR or Gemini Vision) to parse delivery challans into structured JSON.
    Strictly NO hardcoded mock data in production path.
    """
    img_size = len(image_bytes)
    logger.info(f"📸 [{request_id}] vision_extract start: image_size={img_size} bytes")
    
    if img_size < 100:
        logger.warning(f"⚠️ [{request_id}] vision_extract error: image file size {img_size} bytes is too small")
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message="Uploaded image file is empty or too small",
            status_code=400
        )

    api_key = settings.get_vision_api_key()
    if not api_key:
        logger.error(f"❌ [{request_id}] GOOGLE_VISION_API_KEY / GEMINI_API_KEY is not configured in backend/.env")
        raise AppException(
            code=ErrorCode.SARVAM_API_ERROR,
            message="GOOGLE_VISION_API_KEY or GEMINI_API_KEY is not set in backend/.env. Please set a valid API key.",
            status_code=400
        )

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    # Strategy 1: Try Google Cloud Vision OCR API (vision.googleapis.com)
    cloud_vision_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    cloud_vision_payload = {
        "requests": [
            {
                "image": {"content": b64_image},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
            }
        ]
    }

    raw_ocr_text = ""
    
    logger.info(f"🎯 [{request_id}] vision_extract: calling Google Cloud Vision API (vision.googleapis.com)...")
    try:
        response = httpx.post(cloud_vision_url, json=cloud_vision_payload, timeout=45.0)
        if response.status_code == 200:
            res_json = response.json()
            responses = res_json.get("responses", [])
            if responses:
                err = responses[0].get("error")
                if err:
                    logger.warning(f"⚠️ [{request_id}] Cloud Vision API error details: {err}")
                else:
                    full_text_annotation = responses[0].get("fullTextAnnotation", {})
                    raw_ocr_text = full_text_annotation.get("text", "").strip()
    except Exception as exc:
        logger.warning(f"⚠️ [{request_id}] Cloud Vision API call exception: {exc}")

    # Strategy 2: If Cloud Vision API didn't return text (or key is for Gemini), try Gemini Vision API
    if not raw_ocr_text:
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        gemini_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": VISION_CHALLAN_EXTRACTION_PROMPT},
                        {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}}
                    ]
                }
            ],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}
        }
        logger.info(f"🎯 [{request_id}] vision_extract: calling Gemini Vision API (generativelanguage.googleapis.com)...")
        try:
            gem_res = httpx.post(gemini_url, json=gemini_payload, timeout=45.0)
            if gem_res.status_code == 200:
                candidates = gem_res.json().get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        raw_ocr_text = parts[0].get("text", "").strip()
            else:
                logger.error(f"❌ [{request_id}] Gemini Vision API HTTP status {gem_res.status_code}: {gem_res.text}")
        except Exception as exc:
            logger.error(f"❌ [{request_id}] Gemini Vision API exception: {exc}")

    if not raw_ocr_text:
        raise AppException(
            code=ErrorCode.SARVAM_API_ERROR,
            message="Google Vision API call failed or returned empty text. Please ensure Google Cloud Vision API or Generative Language API is enabled.",
            status_code=400
        )

    # CRITICAL LOGGING REQUIREMENT: Log raw unparsed OCR response text
    logger.info(f"📝 [{request_id}] vision_extract: raw response = {raw_ocr_text}")

    # Parse response (JSON or structured OCR text)
    try:
        cleaned_json = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw_ocr_text, flags=re.MULTILINE).strip()
        parsed_data = json.loads(cleaned_json)
        
        raw_items = parsed_data.get("line_items", [])
        normalized_items = []
        calculated_total = 0.0

        for item in raw_items:
            norm_sku = normalize_sku(item.get("sku", ""))
            qty = int(round(float(item.get("quantity", 1))))
            price = float(item.get("unit_price", 0.0))
            calculated_total += qty * price
            normalized_items.append({"sku": norm_sku, "quantity": qty, "unit_price": price})

        result = {
            "distributor_name_guess": str(parsed_data.get("distributor_name_guess", "Unknown Distributor")).strip(),
            "line_items": normalized_items,
            "total_amount": float(parsed_data.get("total_amount", calculated_total)),
            "extraction_confidence": float(parsed_data.get("extraction_confidence", 0.85))
        }
    except Exception:
        # Fallback to OCR text parsing if raw_ocr_text is plain OCR text
        result = parse_ocr_text_to_challan_json(raw_ocr_text)

    logger.info(f"🔍 [{request_id}] vision_extract complete: distributor='{result['distributor_name_guess']}', items_count={len(result['line_items'])}, total_amount=₹{result['total_amount']}, confidence={result['extraction_confidence']}")
    return result
