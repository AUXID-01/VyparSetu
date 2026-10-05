import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.models import Invoice, Alert, OutboxEvent
from core.ids import generate_id
from core.errors import AppException
from core.logging import get_logger
from workers.context import get_worker_db
from services.challan_service import get_merchant_available_settlement_balance

logger = get_logger("workers.payout_worker")

def settle_vendor_invoice(invoice_id: str, merchant_id: str) -> dict:
    """
    Native settlement processor replacing external n8n payout webhooks.
    Executes:
      1. Invoice existence & ownership validation.
      2. Payout ceiling safety check (<= ₹10,000).
      3. Available settlement balance validation.
      4. Bank UTR simulation & database settlement commit.
      5. Synchronous outbox record creation.
    """
    logger.info(f"💸 [Payout Worker] Processing vendor payout for invoice='{invoice_id}', merchant='{merchant_id}'")
    
    with get_worker_db() as db:
        invoice = db.query(Invoice).filter(
            Invoice.invoice_id == invoice_id,
            Invoice.merchant_id == merchant_id
        ).first()
        
        if not invoice:
            raise AppException(
                code="INVOICE_NOT_FOUND",
                message=f"Invoice '{invoice_id}' not found for merchant '{merchant_id}'",
                status_code=404
            )
            
        if invoice.is_paid:
            logger.info(f"ℹ️ [Payout Worker] Invoice '{invoice_id}' is already settled (UTR: {invoice.payout_reference})")
            return {
                "payout_status": "SUCCEEDED",
                "payout_reference": invoice.payout_reference,
                "invoice_id": invoice.invoice_id,
                "amount": float(invoice.total_amount),
                "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None
            }
            
        amount_float = float(invoice.total_amount)
        
        # 1. Payout Ceiling Guard (replaces n8n If node condition)
        if amount_float > 10000.0:
            logger.warning(f"⚠️ [Payout Worker] Invoice amount {amount_float} exceeds ceiling limit of 10000.0")
            alert = Alert(
                alert_id=generate_id("alrt_"),
                merchant_id=merchant_id,
                alert_type="PAYOUT_FAILED",
                details={
                    "invoice_id": invoice.invoice_id,
                    "amount": amount_float,
                    "failure_reason": "Daily payout ceiling of 10,000 exceeded"
                }
            )
            db.add(alert)
            return {
                "payout_status": "FAILED",
                "failure_reason": "Daily payout ceiling of 10,000 exceeded",
                "invoice_id": invoice.invoice_id,
                "amount": amount_float
            }
            
        # 2. Settlement Balance Check
        available_balance = get_merchant_available_settlement_balance(db, merchant_id)
        if Decimal(str(invoice.total_amount)) > available_balance:
            logger.warning(f"⚠️ [Payout Worker] Insufficient settlement funds (Needed: {invoice.total_amount}, Available: {available_balance})")
            raise AppException(
                code="INSUFFICIENT_FUNDS",
                message="Settlement balance insufficient to clear payout",
                status_code=400
            )
            
        # 3. Simulate Banking UTR & Update Invoice
        utr = f"PAYTM_UTR_{uuid.uuid4().hex[:8].upper()}"
        now_dt = datetime.now(timezone.utc)
        
        invoice.is_paid = True
        invoice.paid_at = now_dt
        invoice.payout_reference = utr
        
        # 4. Outbox Event (Audited status transition)
        outbox_event = OutboxEvent(
            event_id=generate_id("out_"),
            merchant_id=merchant_id,
            event_type="PAYOUT_SETTLED",
            payload={
                "invoice_id": invoice.invoice_id,
                "amount": amount_float,
                "utr_reference": utr,
                "distributor_id": invoice.distributor_id
            },
            status="SYNCED",
            synced_at=now_dt
        )
        db.add(outbox_event)
        
        logger.info(f"✅ [Payout Worker] Successfully settled invoice='{invoice_id}' with UTR='{utr}'")
        
        return {
            "payout_status": "SUCCEEDED",
            "payout_reference": utr,
            "invoice_id": invoice.invoice_id,
            "amount": amount_float,
            "paid_at": now_dt.isoformat()
        }
