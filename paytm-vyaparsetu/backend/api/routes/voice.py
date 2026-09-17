from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from api.deps import get_db
from services import voice_service
from core.errors import success_envelope

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
