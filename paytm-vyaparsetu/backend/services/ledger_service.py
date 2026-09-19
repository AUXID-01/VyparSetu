from sqlalchemy.orm import Session
from typing import Optional
from db.models import LedgerTransaction, OutboxEvent, Customer
from core.enums import TxnType, LedgerSource, OutboxStatus, OutboxEventType
from core.errors import AppException, ErrorCode
from core.ids import generate_id

def record_customer_payment(
    db: Session, 
    merchant_id: str, 
    customer_id: str, 
    amount: float, 
    source: str = LedgerSource.MANUAL.value, 
    payment_reference: Optional[str] = None
) -> dict:
    
    if amount <= 0:
        raise AppException(ErrorCode.VALIDATION_ERROR, "Payment amount must be greater than zero", 400)
        
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id,
        Customer.merchant_id == merchant_id
    ).first()
    
    if not customer:
        raise AppException(ErrorCode.CUSTOMER_NOT_FOUND, "Customer not found", 404)
        
    txn_id = generate_id("txn_")
    
    txn = LedgerTransaction(
        txn_id=txn_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        amount=amount,
        txn_type=TxnType.CREDIT_PAID.value,
        source=source,
        items=[]
    )
    db.add(txn)
    
    outbox_id = generate_id("obx_")
    outbox = OutboxEvent(
        event_id=outbox_id,
        merchant_id=merchant_id,
        event_type=OutboxEventType.CUSTOMER_PAYMENT_SETTLED.value,
        payload={
            "txn_id": txn_id,
            "customer_id": customer_id,
            "amount": float(amount),
            "payment_reference": payment_reference,
            "customer_name": customer.display_name
        },
        status=OutboxStatus.PENDING.value
    )
    db.add(outbox)
    
    db.commit()
    
    return {
        "txn_id": txn_id,
        "amount": amount,
        "customer_id": customer_id,
        "status": "SUCCESS"
    }
