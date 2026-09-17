from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from api.deps import get_db
from services import voice_service
import sarvam
from core.errors import success_envelope, AppException, ErrorCode

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
def log_credit(req: LogCreditReq, db: Session = Depends(get_db)):
    result = voice_service.process_log_credit(
        db=db,
        merchant_id=req.merchant_id,
        customer_name=req.extracted.customer_name,
        amount=req.extracted.amount,
        items=req.extracted.items,
        confidence=req.extracted.confidence
    )
    return success_envelope(result)

@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message="Uploaded audio file is empty",
            status_code=400
        )
    
    filename = audio.filename or "audio.wav"
    res = sarvam.transcribe_audio(audio_bytes, filename=filename)
    
    return success_envelope({
        "transcript": res["transcript"],
        "language_detected": res["language_code"]
    })

@router.post("/log-credit-from-audio")
async def log_credit_from_audio(
    merchant_id: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    audio_bytes = await audio.read()
    filename = audio.filename or "audio.wav"
    
    result = voice_service.process_voice_credit_audio(
        db=db,
        merchant_id=merchant_id,
        audio_bytes=audio_bytes,
        filename=filename
    )
    
    return success_envelope(result)
