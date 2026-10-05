from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from api.deps import get_db
from services import voice_service
import sarvam
from core.errors import success_envelope, AppException, ErrorCode
from core.logging import get_logger

logger = get_logger("api.routes.voice")
router = APIRouter()

class ExtractedData(BaseModel):
    customer_name: str
    amount: float
    items: List[str]
    confidence: float

class LogCreditReq(BaseModel):
    merchant_id: str
    raw_transcript: str
    extracted: ExtractedData

@router.post("/log-credit")
def log_credit(req: LogCreditReq, request: Request, db: Session = Depends(get_db)):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"[{req_id}] POST /voice/log-credit ingress: merchant_id='{req.merchant_id}', customer='{req.extracted.customer_name}', amount={req.extracted.amount}")
    
    result = voice_service.process_log_credit(
        db=db,
        merchant_id=req.merchant_id,
        customer_name=req.extracted.customer_name,
        amount=req.extracted.amount,
        items=req.extracted.items,
        confidence=req.extracted.confidence,
        request_id=req_id
    )
    logger.info(f"[{req_id}] POST /voice/log-credit egress: txn_id='{result.get('txn_id')}'")
    return success_envelope(result)

@router.post("/transcribe")
async def transcribe(request: Request, audio: UploadFile = File(...)):
    req_id = getattr(request.state, "request_id", "N/A")
    filename = audio.filename or "audio.wav"
    logger.info(f"[{req_id}] POST /voice/transcribe ingress: filename='{filename}'")
    
    audio_bytes = await audio.read()
    if not audio_bytes:
        logger.warning(f"[{req_id}] POST /voice/transcribe error: uploaded audio file is empty")
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message="Uploaded audio file is empty",
            status_code=400
        )
    
    res = sarvam.transcribe_audio(audio_bytes, filename=filename, request_id=req_id)
    
    logger.info(f"[{req_id}] POST /voice/transcribe egress: transcript='{res['transcript']}'")
    return success_envelope({
        "transcript": res["transcript"],
        "language_detected": res["language_code"]
    })

class ConfirmCreditReq(BaseModel):
    merchant_id: str
    confirmation_token: str
    confirmed: bool

@router.post("/confirm-credit")
def confirm_credit(req: ConfirmCreditReq, request: Request, db: Session = Depends(get_db)):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"[{req_id}] POST /voice/confirm-credit ingress: merchant_id='{req.merchant_id}', confirmed={req.confirmed}")
    
    result = voice_service.confirm_credit(
        db=db,
        merchant_id=req.merchant_id,
        token=req.confirmation_token,
        confirmed=req.confirmed,
        request_id=req_id
    )
    
    return success_envelope(result)

@router.post("/log-credit-from-audio")
async def log_credit_from_audio(
    request: Request,
    merchant_id: str = Form(...),
    language_override: str = Form(None),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    req_id = getattr(request.state, "request_id", "N/A")
    filename = audio.filename or "audio.wav"
    logger.info(f"[{req_id}] POST /voice/log-credit-from-audio ingress: merchant_id='{merchant_id}', lang_override='{language_override}', filename='{filename}'")
    
    audio_bytes = await audio.read()
    
    result = voice_service.process_voice_credit_audio(
        db=db,
        merchant_id=merchant_id,
        audio_bytes=audio_bytes,
        language_override=language_override,
        filename=filename,
        request_id=req_id
    )
    
    logger.info(f"[{req_id}] POST /voice/log-credit-from-audio egress: outcome='{result.get('outcome')}'")
    return success_envelope(result)

