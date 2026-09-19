from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from api.deps import get_db
from services import ledger_service
from core.errors import success_envelope
from core.logging import get_logger

logger = get_logger("api.routes.payments")
router = APIRouter()

class MockWebhookReq(BaseModel):
    merchant_id: str
    customer_id: str
    amount: float
    payment_reference: str
    status: str = "SUCCESS"

@router.post("/mock-webhook")
def mock_payment_webhook(req: MockWebhookReq, db: Session = Depends(get_db)):
    """Simulates an inbound payment link webhook from n8n / payment gateway"""
    logger.info(f"Received mock webhook for payment {req.payment_reference}, status={req.status}")
    
    if req.status == "SUCCESS":
        result = ledger_service.record_customer_payment(
            db=db,
            merchant_id=req.merchant_id,
            customer_id=req.customer_id,
            amount=req.amount,
            source="PAYMENT_LINK",
            payment_reference=req.payment_reference
        )
        return success_envelope(result)
        
    return success_envelope({"status": "IGNORED", "reason": f"Payment status was {req.status}"})
