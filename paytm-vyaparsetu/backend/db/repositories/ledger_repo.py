from sqlalchemy.orm import Session
from db.models import LedgerTransaction
from core.ids import generate_txn_id
from typing import List, Optional

def create_transaction(
    db: Session, 
    merchant_id: str, 
    customer_id: str, 
    amount: float, 
    txn_type: str, 
    source: str,
    items: Optional[List[str]] = None,
    extraction_confidence: Optional[float] = None
) -> LedgerTransaction:
    txn = LedgerTransaction(
        txn_id=generate_txn_id(),
        merchant_id=merchant_id,
        customer_id=customer_id,
        amount=amount,
        txn_type=txn_type,
        source=source,
        items=items or [],
        extraction_confidence=extraction_confidence
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn

insert_transaction = create_transaction

def calculate_customer_due(db: Session, merchant_id: str, customer_id: str) -> float:
    from sqlalchemy.sql import func
    from core.enums import TxnType
    
    total_due = db.query(func.sum(LedgerTransaction.amount)).filter(
        LedgerTransaction.customer_id == customer_id,
        LedgerTransaction.merchant_id == merchant_id,
        LedgerTransaction.txn_type == TxnType.CREDIT_ADDED.value
    ).scalar() or 0.0

    total_paid = db.query(func.sum(LedgerTransaction.amount)).filter(
        LedgerTransaction.customer_id == customer_id,
        LedgerTransaction.merchant_id == merchant_id,
        LedgerTransaction.txn_type == TxnType.CREDIT_PAID.value
    ).scalar() or 0.0

    return float(total_due) - float(total_paid)

