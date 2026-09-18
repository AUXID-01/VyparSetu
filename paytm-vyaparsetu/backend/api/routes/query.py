from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date
from api.deps import get_db
from db.models import LedgerTransaction, Customer, Invoice, Distributor
from core.errors import success_envelope, AppException, ErrorCode
from core.enums import TxnType
from pydantic import BaseModel
from fastapi import Request
from core.logging import get_logger
from services.query_service import answer_grounded_question

logger = get_logger("api.routes.query")

class QARequest(BaseModel):
    merchant_id: str
    question: str

router = APIRouter()

@router.post("/ask")
async def ask_grounded_question(
    request: Request,
    payload: QARequest,
    db: Session = Depends(get_db)
):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] POST /api/v1/query/ask ingress: {payload.model_dump()}")
    
    result = await answer_grounded_question(
        db=db, 
        merchant_id=payload.merchant_id, 
        question=payload.question
    )
    
    logger.info(f"📤 [{req_id}] [JSON Payload] POST /api/v1/query/ask egress: {result}")
    return success_envelope(result)

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

@router.get("/customers")
def get_customers(merchant_id: str, db: Session = Depends(get_db)):
    customers = db.query(Customer).filter(Customer.merchant_id == merchant_id).all()
    result = []
    
    for customer in customers:
        total_due = db.query(func.sum(LedgerTransaction.amount)).filter(
            LedgerTransaction.customer_id == customer.customer_id,
            LedgerTransaction.txn_type == TxnType.CREDIT_ADDED.value
        ).scalar() or 0.0
        
        total_paid = db.query(func.sum(LedgerTransaction.amount)).filter(
            LedgerTransaction.customer_id == customer.customer_id,
            LedgerTransaction.txn_type == TxnType.CREDIT_PAID.value
        ).scalar() or 0.0
        
        last_txn = db.query(LedgerTransaction).filter(
            LedgerTransaction.customer_id == customer.customer_id
        ).order_by(LedgerTransaction.created_at.desc()).first()
        
        net_due = float(total_due) - float(total_paid)
        
        result.append({
            "customer_id": customer.customer_id,
            "display_name": customer.display_name,
            "phone": customer.phone or "",
            "total_due": net_due,
            "total_credits": float(total_due),
            "total_paid": float(total_paid),
            "last_active": last_txn.created_at.isoformat() if last_txn else customer.created_at.isoformat(),
            "items_summary": last_txn.items if last_txn and last_txn.items else []
        })
        
    result.sort(key=lambda x: x["total_due"], reverse=True)
    return success_envelope(result)

@router.get("/recent-transactions")
def get_recent_transactions(merchant_id: str, limit: int = 20, db: Session = Depends(get_db)):
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
            "source": txn.source,
            "items": txn.items or [],
            "extraction_confidence": float(txn.extraction_confidence) if txn.extraction_confidence else 1.0,
            "created_at": txn.created_at.isoformat()
        })
        
    return success_envelope(result)

@router.get("/settlements")
def get_settlements(merchant_id: str, db: Session = Depends(get_db)):
    invoices = db.query(Invoice).join(Distributor).filter(
        Invoice.merchant_id == merchant_id
    ).order_by(Invoice.created_at.desc()).all()
    
    result = []
    for inv in invoices:
        result.append({
            "invoice_id": inv.invoice_id,
            "distributor_name": inv.distributor.name,
            "total_amount": float(inv.total_amount),
            "is_paid": inv.is_paid,
            "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            "payout_reference": inv.payout_reference,
            "created_at": inv.created_at.isoformat(),
            "payment_handle_type": inv.payment_handle_type,
            "payment_handle_value": inv.payment_handle_value,
            "challan_type": inv.challan_type
        })
        
    return success_envelope(result)
