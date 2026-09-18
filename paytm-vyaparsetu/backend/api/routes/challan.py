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

    logger.info(f"✨ [{req_id}] POST /challan/extract egress: distributor='{result.distributor_name_raw}', items={len(result.line_items)}")
    return success_envelope(result.model_dump())
