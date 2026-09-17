from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from db.repositories import customers_repo, ledger_repo, outbox_repo
from core.enums import TxnType, LedgerSource, OutboxEventType
from db.models import LedgerTransaction

def process_log_credit(
    db: Session,
    merchant_id: str,
    customer_name: str,
    amount: float,
    items: list[str],
    confidence: float
) -> dict:
    
    # 1. Resolve/create customer
    customer = customers_repo.get_or_create(db, merchant_id, customer_name)
    
    # 2. Insert ledger transaction
    txn = ledger_repo.create_transaction(
        db=db,
        merchant_id=merchant_id,
        customer_id=customer.customer_id,
        amount=amount,
        txn_type=TxnType.CREDIT_ADDED.value,
        source=LedgerSource.VOICE.value,
        items=items,
        extraction_confidence=confidence
    )
    
    # 3. Insert outbox_events row
    outbox_repo.create_event(
        db=db,
        merchant_id=merchant_id,
        event_type=OutboxEventType.CREDIT_ADDED.value,
        payload={
            "txn_id": txn.txn_id,
            "customer_id": customer.customer_id,
            "merchant_id": merchant_id,
            "amount": amount
        }
    )
    
    # Compute new total due
    total_due = db.query(func.sum(LedgerTransaction.amount)).filter(
        LedgerTransaction.customer_id == customer.customer_id,
        LedgerTransaction.merchant_id == merchant_id,
        LedgerTransaction.txn_type == TxnType.CREDIT_ADDED.value
    ).scalar() or 0.0
    
    total_paid = db.query(func.sum(LedgerTransaction.amount)).filter(
        LedgerTransaction.customer_id == customer.customer_id,
        LedgerTransaction.merchant_id == merchant_id,
        LedgerTransaction.txn_type == TxnType.CREDIT_PAID.value
    ).scalar() or 0.0
    
    current_balance = float(total_due) - float(total_paid)
    
    # Confirmation text
    confirmation_text = f"{customer.display_name} ji ke khate mein {amount} rupaye jod diye gaye hain."
    
    return {
        "txn_id": txn.txn_id,
        "customer_id": customer.customer_id,
        "new_balance": current_balance,
        "confirmation_audio_text": confirmation_text
    }
