import hashlib
import time
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models import LedgerTransaction, Customer, InvoiceLineItem, Invoice, Distributor
from db.repositories import insight_cache_repo
from core.logging import get_logger

logger = get_logger("services.query_service")

async def answer_grounded_question(db: Session, merchant_id: str, question: str) -> dict:
    """Answers a question using Cache first, falling back to native PostgreSQL."""
    
    # 1. Deterministic Cache Key
    question_hash = hashlib.sha256(question.strip().lower().encode()).hexdigest()[:12]
    cache_key = f"qa_{merchant_id}_{question_hash}"
    
    # 2. Check Cache
    cached = insight_cache_repo.get_cached_insight(db, cache_key)
    if cached:
        logger.info(f"⚡ [Query Service] Cache HIT for question: '{question[:30]}...'")
        return {
            "answer": cached.result.get("answer", ""),
            "source": "CACHE",
            "generated_in_ms": 0
        }
        
    logger.info(f"🌐 [Query Service] Cache MISS. Routing to Native PostgreSQL for: '{question[:30]}...'")
    start_time = time.time()
    
    answer_text = ""
    q_lower = question.lower()
    
    # 3. Native Database Routing Logic based on basic intent mapping
    if any(keyword in q_lower for keyword in ["balance", "ledger", "credit", "udhaar", "due"]):
        # Query ledger balances
        result = db.query(
            Customer.display_name,
            func.sum(
                func.case(
                    (LedgerTransaction.txn_type == 'CREDIT_ADDED', LedgerTransaction.amount),
                    (LedgerTransaction.txn_type == 'CREDIT_PAID', -LedgerTransaction.amount),
                    else_=0
                )
            ).label('balance')
        ).join(
            LedgerTransaction, Customer.customer_id == LedgerTransaction.customer_id
        ).filter(
            Customer.merchant_id == merchant_id
        ).group_by(Customer.display_name).all()
        
        if result:
            answer_text = "Customer Balances:\n" + "\n".join([f"- {r.display_name}: ₹{r.balance:.2f}" for r in result if r.balance and r.balance > 0])
        else:
            answer_text = "No outstanding balances found."
            
    elif any(keyword in q_lower for keyword in ["rate", "invoice", "price", "sku", "cost"]):
        # Query latest rates
        result = db.query(
            InvoiceLineItem.sku,
            InvoiceLineItem.unit_price,
            Distributor.name
        ).join(
            Invoice, Invoice.invoice_id == InvoiceLineItem.invoice_id
        ).join(
            Distributor, Distributor.distributor_id == Invoice.distributor_id
        ).filter(
            Invoice.merchant_id == merchant_id
        ).order_by(Invoice.created_at.desc()).limit(10).all()
        
        if result:
            answer_text = "Recent Item Rates:\n" + "\n".join([f"- {r.sku} (from {r.name}): ₹{r.unit_price:.2f}" for r in result])
        else:
            answer_text = "No recent invoices or item rates found."
    else:
        answer_text = "Sorry, I could not map your question to the existing database records. Please ask about customer balances or item rates."
        
    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(f"✅ [Query Service] Native query completed in {elapsed_ms}ms")
        
    # 4. Persist to cache
    result_dict = {"answer": answer_text}
    insight_cache_repo.save_insight(
        db=db,
        cache_key=cache_key,
        merchant_id=merchant_id,
        insight_type="QA_ANSWER",
        result=result_dict
    )
    
    return {
        "answer": answer_text,
        "source": "LIVE",
        "generated_in_ms": elapsed_ms
    }
