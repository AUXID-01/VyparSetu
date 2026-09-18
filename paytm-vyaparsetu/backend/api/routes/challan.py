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
    image: UploadFile = File(...)
):
    """
    Exposes POST /api/v1/challan/extract (Passthrough debug & preview endpoint).
    Accepts image upload, extracts structured challan JSON, and logs raw responses.
    Does NOT write to PostgreSQL.
    """
    req_id = getattr(request.state, "request_id", "N/A")
    filename = image.filename or "challan.jpg"
    logger.info(f"📄 [{req_id}] POST /challan/extract ingress: merchant_id='{merchant_id}', filename='{filename}'")

    image_bytes = await image.read()
    if not image_bytes or len(image_bytes) < 10:
        logger.warning(f"⚠️ [{req_id}] POST /challan/extract error: uploaded image file is empty or corrupted")
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message="Uploaded image file is empty or corrupted",
            status_code=400
        )

    extraction_result = vision.extract_challan(image_bytes, request_id=req_id)

    logger.info(f"✨ [{req_id}] POST /challan/extract egress: distributor='{extraction_result.get('distributor_name_guess')}', items={len(extraction_result.get('line_items', []))}")
    return success_envelope(extraction_result)
