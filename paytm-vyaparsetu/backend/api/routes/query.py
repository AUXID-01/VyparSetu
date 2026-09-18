from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date
from api.deps import get_db
from db.models import LedgerTransaction, Customer
from core.errors import success_envelope, AppException, ErrorCode
from core.enums import TxnType

router = APIRouter()

@router.get("/customer-due/{customer_id}")
def get_customer_due(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise AppException(ErrorCode.CUSTOMER_NOT_FOUND, "Customer not found", 404)
        
    total_due = db.query(func.sum(LedgerTransaction.amount)).filter(
        LedgerTransaction.customer_id == customer_id,
        LedgerTransaction.txn_type == TxnType.CREDIT_ADDED.value
    ).scalar() or 0.0
    
    total_paid = db.query(func.sum(LedgerTransaction.amount)).filter(
        LedgerTransaction.customer_id == customer_id,
        LedgerTransaction.txn_type == TxnType.CREDIT_PAID.value
    ).scalar() or 0.0
    
    current_balance = float(total_due) - float(total_paid)
    
    return success_envelope({
        "customer_id": customer.customer_id,
        "display_name": customer.display_name,
        "total_due": current_balance
    })

@router.get("/daily-summary")
def get_daily_summary(merchant_id: str, date: date, db: Session = Depends(get_db)):
    total_credits = db.query(func.sum(LedgerTransaction.amount)).filter(
        LedgerTransaction.merchant_id == merchant_id,
        LedgerTransaction.txn_type == TxnType.CREDIT_ADDED.value,
        func.date(LedgerTransaction.created_at) == date
    ).scalar() or 0.0
    
    total_payments = db.query(func.sum(LedgerTransaction.amount)).filter(
        LedgerTransaction.merchant_id == merchant_id,
        LedgerTransaction.txn_type == TxnType.CREDIT_PAID.value,
        func.date(LedgerTransaction.created_at) == date
    ).scalar() or 0.0
    
    return success_envelope({
        "merchant_id": merchant_id,
        "date": date.isoformat(),
        "total_credits_added": float(total_credits),
        "total_payments_received": float(total_payments)
    })

@router.get("/recent-transactions")
def get_recent_transactions(merchant_id: str, limit: int = 5, db: Session = Depends(get_db)):
    txns = db.query(LedgerTransaction).filter(
        LedgerTransaction.merchant_id == merchant_id
    ).order_by(LedgerTransaction.created_at.desc()).limit(limit).all()
    
    result = []
    for txn in txns:
        customer = db.query(Customer).filter(Customer.customer_id == txn.customer_id).first()
        result.append({
            "txn_id": txn.txn_id,
            "customer_id": txn.customer_id,
            "customer_name": customer.display_name if customer else "Unknown",
            "amount": float(txn.amount),
            "txn_type": txn.txn_type,
            "created_at": txn.created_at.isoformat()
        })
        
    return success_envelope(result)
