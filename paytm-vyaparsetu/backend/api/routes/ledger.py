from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from api.deps import get_db, get_current_merchant
from core.errors import success_envelope
from services import ledger_service

router = APIRouter()

class RecordPaymentReq(BaseModel):
    customer_id: str
    amount: float
    payment_reference: Optional[str] = None
    source: Optional[str] = "MANUAL"

@router.post("/record-payment")
def record_payment(req: RecordPaymentReq, db: Session = Depends(get_db), merchant_id: str = Depends(get_current_merchant)):
    result = ledger_service.record_customer_payment(
        db=db,
        merchant_id=merchant_id,
        customer_id=req.customer_id,
        amount=req.amount,
        source=req.source,
        payment_reference=req.payment_reference
    )
    return success_envelope(result)
