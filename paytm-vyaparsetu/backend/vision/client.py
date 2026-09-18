import base64
import json
import re
import httpx
from typing import Tuple, Dict, Any

from config import settings
from core.errors import AppException, ErrorCode
from core.logging import get_logger
from .prompts import VISION_CHALLAN_EXTRACTION_PROMPT
from .schemas import ChallanExtractionResult, ChallanType
from .preprocessor import preprocess_challan_image
from .ocr_grounding import get_ocr_grounding

logger = get_logger("vision.client")

def _call_groq_vision(b64_image: str, ocr_text: str, request_id: str) -> Tuple[Dict[str, Any], str]:
    """Tier 1: Fast/Cost-effective model (Groq)."""
    api_key = settings.GROQ_API_KEY
    if not api_key:
        logger.error(f"❌ [{request_id}] GROQ_API_KEY missing.")
        raise AppException(code="VISION_API_ERROR", message="GROQ_API_KEY missing", status_code=500)
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    prompt = VISION_CHALLAN_EXTRACTION_PROMPT + f"\n\n--- OCR GROUNDING TEXT ---\n{ocr_text}"
    
    payload = {
        "model": "groq/compound",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"🎯 [{request_id}] Calling Tier 1 (Groq Vision)...")
    res = httpx.post(url, json=payload, headers=headers, timeout=90.0)
    if res.status_code == 200:
        data = res.json()
        content = data["choices"][0]["message"]["content"]
        cleaned_json = re.sub(r'^```(?:json)?\s*|\s*```$', '', content, flags=re.MULTILINE).strip()
        return json.loads(cleaned_json), data
    else:
        err_msg = res.text
        logger.error(f"❌ [{request_id}] Groq API Error {res.status_code}: {err_msg}")
        raise AppException(code="VISION_API_ERROR", message=f"Groq API failed: {err_msg}", status_code=502)

def _call_openai_vision(b64_image: str, ocr_text: str, request_id: str) -> Tuple[Dict[str, Any], str]:
    """Tier 2: Escalation to Frontier Model (GPT-4o)."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        logger.error(f"❌ [{request_id}] OPENAI_API_KEY missing. Cannot escalate.")
        raise Exception("OPENAI_API_KEY missing")
        
    url = "https://api.openai.com/v1/chat/completions"
    prompt = VISION_CHALLAN_EXTRACTION_PROMPT + f"\n\n--- OCR GROUNDING TEXT ---\n{ocr_text}"
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"🚀 [{request_id}] Calling Tier 2 (OpenAI GPT-4o)...")
    res = httpx.post(url, json=payload, headers=headers, timeout=60.0)
    if res.status_code == 200:
        data = res.json()
        content = data["choices"][0]["message"]["content"]
        cleaned_json = re.sub(r'^```(?:json)?\s*|\s*```$', '', content, flags=re.MULTILINE).strip()
        return json.loads(cleaned_json), data
    else:
        err_msg = res.text
        logger.error(f"❌ [{request_id}] OpenAI API Error {res.status_code}: {err_msg}")
        raise AppException(code="VISION_API_ERROR", message=f"OpenAI API failed: {err_msg}", status_code=502)



def extract_challan_pipeline(
    image_bytes: bytes, 
    capture_medium: str = "CAMERA_PHOTO", 
    request_id: str = "N/A"
) -> Tuple[ChallanExtractionResult, str, dict, str, bool]:
    """
    Executes the 4-stage pipeline for Challan extraction.
    Returns: (ChallanExtractionResult, ocr_raw_text, raw_llm_response, model_used, escalated)
    """
    # Stage A: Preprocessing
    color_bytes, gray_bytes, preprocessed_meta = preprocess_challan_image(image_bytes)
    
    # Stage B: OCR Grounding
    ocr_result = get_ocr_grounding(color_bytes, request_id)
    ocr_text = ocr_result.full_text
    
    b64_color = base64.b64encode(color_bytes).decode('utf-8')
    
    # Stage C: Vision LLM Structuring & Routing
    escalated = False
    model_used = "groq/llama-3.2-vision"
    
    try:
        parsed_json, raw_response = _call_groq_vision(b64_color, ocr_text, request_id)
    except AppException as e:
        logger.error(f"❌ [{request_id}] Vision API Exception: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"❌ [{request_id}] Unexpected Pipeline Error: {str(e)}", exc_info=True)
        raise AppException(code="EXTRACTION_FAILED", message=f"Extraction pipeline failed: {str(e)}", status_code=500)
    
    # Evaluate Escalation Criteria if Tier 1 succeeded
    if not escalated:
        overall_confidence = parsed_json.get("overall_confidence", 0.0)
        challan_type = parsed_json.get("challan_type", ChallanType.UNKNOWN)
        total_payable = parsed_json.get("total_payable", 0.0)
        
        needs_escalation = False
        reason = ""
        
        if overall_confidence < 0.75:
            needs_escalation = True
            reason = f"Low confidence ({overall_confidence})"
        elif challan_type == ChallanType.HANDWRITTEN_SCRAP:
            needs_escalation = True
            reason = "Handwritten format"
        elif total_payable > 5000.00:
            needs_escalation = True
            reason = f"High value invoice (₹{total_payable})"
            
        if needs_escalation:
            logger.info(f"🔄 [{request_id}] Escalation to Tier 2 (Frontier Model) is required for {reason}, but currently DISABLED. Sticking with Tier 1 result.")
            # try:
            #     parsed_json, raw_response = _call_openai_vision(b64_color, ocr_text, request_id)
            #     model_used = "openai/gpt-4o"
            #     escalated = True
            # except Exception as e:
            #     logger.error(f"❌ [{request_id}] Tier 2 failed, falling back to Tier 1 result. Error: {e}")
            #     # We retain the Tier 1 parsed_json if Tier 2 fails

    # Inject capture_medium manually since it comes from the request, not the LLM
    parsed_json["capture_medium"] = capture_medium
    
    # Parse into Pydantic model to ensure strict schema adherence
    result = ChallanExtractionResult(**parsed_json)
    
    logger.info(f"✅ [{request_id}] Pipeline complete. Model: {model_used}, Escalated: {escalated}, Type: {result.challan_type}, Total: ₹{result.total_payable}")
    
    return result, ocr_text, raw_response, model_used, escalated
