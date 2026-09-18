from fastapi import APIRouter, UploadFile, File, Form, Request
from core.errors import success_envelope, AppException, ErrorCode
from core.logging import get_logger
import vision

logger = get_logger("api.routes.challan")

router = APIRouter()

@router.post("/extract")
async def extract_challan_endpoint(
    request: Request,
    merchant_id: str = Form(...),
    image: UploadFile = File(...),
    capture_medium: str = Form("CAMERA_PHOTO")
):
    """
    Exposes POST /api/v1/challan/extract.
    Accepts image upload, runs the 4-stage vision pipeline, and returns the rich ChallanExtractionResult.
    Does NOT write to PostgreSQL.
    """
    req_id = getattr(request.state, "request_id", "N/A")
    filename = image.filename or "challan.jpg"
    logger.info(f"📄 [{req_id}] POST /challan/extract ingress: merchant_id='{merchant_id}', capture_medium='{capture_medium}', filename='{filename}'")

    image_bytes = await image.read()
    if not image_bytes or len(image_bytes) < 10:
        logger.warning(f"⚠️ [{req_id}] POST /challan/extract error: uploaded image file is empty or corrupted")
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message="Uploaded image file is empty or corrupted",
            status_code=400
        )

    result, ocr_text, raw_response, model_used, escalated = vision.extract_challan_pipeline(
        image_bytes=image_bytes,
        capture_medium=capture_medium,
        request_id=req_id
    )

    # We will enrich the response with the raw tracking data so the frontend can send it back to /confirm
    response_data = result.model_dump()
    response_data["ocr_raw_text"] = ocr_text
    response_data["vision_llm_raw_response"] = raw_response
    response_data["model_used"] = model_used
    response_data["escalated"] = escalated

    logger.info(f"✨ [{req_id}] POST /challan/extract egress: distributor='{result.distributor_name_raw}', items={len(result.line_items)}")
    return success_envelope(response_data)


from fastapi import Depends, Body, Request
from sqlalchemy.orm import Session
from api.deps import get_db
from pydantic import BaseModel
from typing import Dict, Any
from services.challan_service import confirm_challan, settle_invoice

class ConfirmPayload(BaseModel):
    merchant_id: str
    data: Dict[str, Any]

class SettlePayload(BaseModel):
    invoice_id: str

@router.post("/confirm")
def confirm_challan_endpoint(
    request: Request,
    payload: ConfirmPayload,
    db: Session = Depends(get_db)
):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"💾 [{req_id}] POST /challan/confirm ingress: merchant_id='{payload.merchant_id}'")
    
    result = confirm_challan(db, payload.merchant_id, payload.data, req_id)
    return success_envelope(result)

@router.post("/settle")
def settle_challan_endpoint(
    request: Request,
    payload: SettlePayload,
    db: Session = Depends(get_db)
):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"💸 [{req_id}] POST /challan/settle ingress: invoice_id='{payload.invoice_id}'")
    
    result = settle_invoice(db, payload.invoice_id, req_id)
    return success_envelope(result)
