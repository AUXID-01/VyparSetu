from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from api.deps import get_db, get_current_merchant
from db.models import LedgerTransaction, OutboxEvent, Customer
from core.enums import TxnType, LedgerSource, OutboxStatus
from core.errors import success_envelope, AppException, ErrorCode
from core.ids import generate_id

router = APIRouter()

class RecordPaymentReq(BaseModel):
    customer_id: str
    amount: float
    payment_reference: Optional[str] = None

@router.post("/record-payment")
def record_payment(req: RecordPaymentReq, db: Session = Depends(get_db), merchant_id: str = Depends(get_current_merchant)):
    # Verify customer belongs to merchant
    customer = db.query(Customer).filter(
        Customer.customer_id == req.customer_id,
        Customer.merchant_id == merchant_id
    ).first()
    
    if not customer:
        raise AppException(ErrorCode.CUSTOMER_NOT_FOUND, "Customer not found", 404)
        
    if req.amount <= 0:
        raise AppException(ErrorCode.VALIDATION_ERROR, "Payment amount must be greater than zero", 400)
        
    txn_id = generate_id("txn_")
    
    txn = LedgerTransaction(
        txn_id=txn_id,
        merchant_id=merchant_id,
        customer_id=req.customer_id,
        amount=req.amount,
        txn_type=TxnType.CREDIT_PAID,
        source=LedgerSource.MANUAL,
        items=[]
    )
    db.add(txn)
    
    outbox_id = generate_id("obx_")
    outbox = OutboxEvent(
        event_id=outbox_id,
        merchant_id=merchant_id,
        event_type="CUSTOMER_PAYMENT_SETTLED",
        payload={
            "txn_id": txn_id,
            "customer_id": req.customer_id,
            "amount": float(req.amount),
            "payment_reference": req.payment_reference
        },
        status=OutboxStatus.PENDING
    )
    db.add(outbox)
    
    db.commit()
    
    return success_envelope({
        "txn_id": txn_id,
        "amount": req.amount,
        "customer_id": req.customer_id,
        "status": "SUCCESS"
    })
