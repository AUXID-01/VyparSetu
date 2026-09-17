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
