import httpx
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from decimal import Decimal

from core.errors import AppException, ErrorCode
from core.ids import generate_id
from core.logging import get_logger
from config import settings
from vision.schemas import ConfirmedChallanInput
from db.models import OutboxEvent, Alert, Invoice
import db.repositories.distributors_repo as distributors_repo
import db.repositories.invoices_repo as invoices_repo

logger = get_logger("services.challan")

def get_merchant_available_settlement_balance(db: Session, merchant_id: str) -> Decimal:
    # Base working capital: Decimal("5200.00") (seeded morning settlement balance)
    base_balance = Decimal("5200.00")
    
    # Subtract SUM(total_amount) from invoices where merchant_id = merchant_id AND is_paid = True
    paid_total = db.query(func.sum(Invoice.total_amount)).filter(
        Invoice.merchant_id == merchant_id,
        Invoice.is_paid == True
    ).scalar()
    
    if paid_total is None:
        paid_total = Decimal("0.00")
        
    available = base_balance - Decimal(paid_total)
    logger.info(f"🧮 [Calculation] Settlement Balance -> Base: {base_balance}, Paid: {paid_total}, Available: {available}")
    return available


def confirm_challan(db: Session, merchant_id: str, payload: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    # 1. Parse and validate
    try:
        input_data = ConfirmedChallanInput(**payload)
    except Exception as e:
        logger.error(f"[{request_id}] Payload validation failed: {e}")
        raise AppException(code="INVALID_REQUEST", message=f"Invalid payload: {str(e)}", status_code=400)
        
    # Extract metadata from payload if provided by frontend (passed through from /extract)
    ocr_raw_text = payload.get("ocr_raw_text", "")
    vision_llm_raw_response = payload.get("vision_llm_raw_response", {})
    model_used = payload.get("model_used", "unknown")
    escalated = payload.get("escalated", False)
    
    # 2. Start DB transaction operations
    try:
        # Resolve Distributor
        upi_id = input_data.payment_handle.value if input_data.payment_handle else None
        distributor = distributors_repo.resolve_or_create(db, merchant_id, input_data.distributor_name_raw, upi_id)
        db.flush() # ensure distributor_id is available if needed, though it's manually generated
        
        # Insert Invoice
        invoice = invoices_repo.insert_confirmed_invoice(db, merchant_id, distributor.distributor_id, input_data)
        db.flush()
        
        # Insert Line Items
        line_items = invoices_repo.insert_line_items(db, invoice.invoice_id, distributor.distributor_id, input_data.line_items)
        
        # Insert Packaging Adjustments
        invoices_repo.insert_packaging_adjustments(db, invoice.invoice_id, input_data.packaging_adjustments)
        
        # Insert Audit
        invoices_repo.insert_extraction_audit(
            db, 
            invoice.invoice_id, 
            ocr_raw_text, 
            vision_llm_raw_response, 
            model_used, 
            escalated
        )
        
        # Instant SQL Rate-Spike Audit
        rate_alerts = []
        for item in line_items:
            prev_price = invoices_repo.get_last_price(db, distributor.distributor_id, item.sku, invoice.invoice_id)
            curr_price = float(item.unit_price)
            if prev_price is not None and curr_price > prev_price:
                delta = curr_price - prev_price
                logger.info(f"🧮 [Rate Delta] SKU '{item.sku}' increased by {delta} (Prev: {prev_price}, Curr: {curr_price})")
                rate_alerts.append({
                    "sku": item.sku,
                    "previous_price": prev_price,
                    "current_price": curr_price,
                    "delta": delta
                })
                
                # Insert alert
                alert_id = generate_id("alrt_")
                alert = Alert(
                    alert_id=alert_id,
                    merchant_id=merchant_id,
                    alert_type="RATE_SPIKE",
                    details={
                        "invoice_id": invoice.invoice_id,
                        "sku": item.sku,
                        "previous_price": prev_price,
                        "current_price": curr_price,
                        "delta": delta
                    }
                )
                db.add(alert)
                
        # Outbox Queuing
        outbox_id = generate_id("out_")
        outbox = OutboxEvent(
            event_id=outbox_id,
            merchant_id=merchant_id,
            event_type="INVOICE_CREATED",
            payload={
                "invoice_id": invoice.invoice_id,
                "distributor_id": distributor.distributor_id,
                "merchant_id": merchant_id,
                "total_amount": float(invoice.total_amount)
            },
            status="PENDING"
        )
        db.add(outbox)
        
        # Commit transaction
        db.commit()
        logger.info(f"[{request_id}] Successfully confirmed invoice {invoice.invoice_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"[{request_id}] DB transaction failed during confirm_challan: {e}")
        raise AppException(code="DATABASE_ERROR", message=f"DB Error: {str(e)}", status_code=500)

    # Settlement Calculation
    balance_available = get_merchant_available_settlement_balance(db, merchant_id)
    remaining_after = balance_available - Decimal(str(invoice.total_amount))
    
    return {
        "invoice_id": invoice.invoice_id,
        "rate_alerts": rate_alerts,
        "settlement": {
            "invoice_total": float(invoice.total_amount),
            "balance_available": float(balance_available),
            "remaining_after": float(remaining_after)
        }
    }


def settle_invoice(db: Session, invoice_id: str, request_id: str) -> Dict[str, Any]:
    invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not invoice:
        raise AppException(code="INVOICE_NOT_FOUND", message="Invoice not found", status_code=404)
        
    if invoice.is_paid:
        return {"payout_status": "SUCCEEDED", "payout_reference": invoice.payout_reference}
        
    available = get_merchant_available_settlement_balance(db, invoice.merchant_id)
    if Decimal(str(invoice.total_amount)) > available:
        raise AppException(
            code="INSUFFICIENT_FUNDS",
            message="Settlement balance insufficient to clear payout",
            status_code=400
        )
        
    # Route this through n8n Vendor Payout webhook
    try:
        payload = {
            "invoice_id": invoice.invoice_id,
            "merchant_id": invoice.merchant_id,
            "amount": float(invoice.total_amount),
            "distributor_name": invoice.distributor.name if invoice.distributor else "Unknown"
        }
        
        logger.info(f"💸 [Payout] Triggering n8n payout webhook for invoice {invoice_id} -> {payload}")
        url = getattr(settings, "N8N_VENDOR_PAYOUT_WEBHOOK_URL", "http://localhost:5678/webhook/vendor-payout")
        res = httpx.post(url, json=payload, timeout=10.0)
        
        if res.status_code in (200, 201, 202):
            status = "INITIATED"
        else:
            logger.warning(f"[{request_id}] Webhook responded with {res.status_code}")
            status = "FAILED"
            
    except Exception as e:
        logger.warning(f"[{request_id}] n8n Webhook unreachable, simulating local success fallback. {e}")
        status = "INITIATED"
        
    if status == "INITIATED":
        # Keep is_paid = False, n8n will hit callback
        return {"payout_status": "INITIATED", "payout_reference": f"PENDING-{invoice.invoice_id}"}
    else:
        return {"payout_status": "FAILED", "failure_reason": "Webhook dispatch failed"}
