import os
import sys
import uuid
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

# Ensure backend root is in sys.path for core imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from core.logging import get_logger

logger = get_logger("mock_paytm")

app = FastAPI(title="Paytm Mock Payout & Balance Gateway", version="1.0.0")

class PayoutRequest(BaseModel):
    invoice_id: str
    distributor_upi_id: str
    amount: float

class PayoutResponse(BaseModel):
    success: bool
    payout_reference: Optional[str] = None
    failure_reason: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok", "service": "mock_paytm"}

@app.get("/balance")
def get_balance():
    logger.info("💳 [MockPaytm] GET /balance requested -> Returning balance ₹5200.00 INR")
    return {"balance": 5200.00, "currency": "INR"}

@app.post("/payout", response_model=PayoutResponse)
def process_payout(req: PayoutRequest):
    logger.info(f"💸 [MockPaytm] POST /payout received: invoice_id='{req.invoice_id}', upi_id='{req.distributor_upi_id}', amount=₹{req.amount}")
    
    if req.amount > 10000.00:
        logger.warning(f"❌ [MockPaytm] Payout rejected: amount ₹{req.amount} exceeds ₹10,000 limit (INSUFFICIENT_FUNDS)")
        return PayoutResponse(
            success=False,
            payout_reference=None,
            failure_reason="INSUFFICIENT_FUNDS"
        )
    
    payout_ref = f"PAYTM-MOCK-{uuid.uuid4().hex[:6].upper()}"
    logger.info(f"✅ [MockPaytm] Payout approved: ref='{payout_ref}', amount=₹{req.amount}")
    return PayoutResponse(
        success=True,
        payout_reference=payout_ref,
        failure_reason=None
    )
