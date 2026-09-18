import base64
import httpx
from config import settings
from core.errors import AppException, ErrorCode
from core.logging import get_logger
from .schemas import OCRGroundingResult

logger = get_logger("vision.ocr")

def get_ocr_grounding(image_bytes: bytes, request_id: str) -> OCRGroundingResult:
    """
    Stage B: Gets OCR text from Google Cloud Vision API.
    """
    api_key = settings.get_vision_api_key()
    if not api_key:
        logger.error(f"❌ [{request_id}] GOOGLE_VISION_API_KEY is missing.")
        raise AppException(
            code=ErrorCode.SARVAM_API_ERROR,
            message="GOOGLE_VISION_API_KEY is not configured.",
            status_code=400
        )
        
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    payload = {
        "requests": [
            {
                "image": {"content": b64_image},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
            }
        ]
    }
    
    full_text = ""
    text_blocks = []
    
    logger.info(f"🎯 [{request_id}] ocr_grounding: calling Google Cloud Vision API...")
    try:
        response = httpx.post(url, json=payload, timeout=45.0)
        if response.status_code == 200:
            res_json = response.json()
            responses = res_json.get("responses", [])
            if responses:
                err = responses[0].get("error")
                if err:
                    logger.warning(f"⚠️ [{request_id}] Cloud Vision API error details: {err}")
                else:
                    full_text_annotation = responses[0].get("fullTextAnnotation", {})
                    full_text = full_text_annotation.get("text", "").strip()
                    
                    # Extract bounding boxes for text blocks
                    pages = full_text_annotation.get("pages", [])
                    for page in pages:
                        for block in page.get("blocks", []):
                            block_text = ""
                            for paragraph in block.get("paragraphs", []):
                                for word in paragraph.get("words", []):
                                    word_text = "".join([symbol.get("text", "") for symbol in word.get("symbols", [])])
                                    block_text += word_text + " "
                                block_text += "\n"
                            
                            text_blocks.append({
                                "text": block_text.strip(),
                                "bounding_box": block.get("boundingBox", {})
                            })
        else:
            logger.error(f"❌ [{request_id}] Cloud Vision API HTTP status {response.status_code}: {response.text}")
    except Exception as exc:
        logger.warning(f"⚠️ [{request_id}] Cloud Vision API call exception: {exc}")
        
    logger.info(f"✅ [{request_id}] [ocr_grounding] Found {len(full_text)} chars from Google Vision")
    
    return OCRGroundingResult(
        full_text=full_text,
        text_blocks=text_blocks,
        avg_confidence=0.90 if full_text else 0.0,
        used=bool(full_text)
    )
