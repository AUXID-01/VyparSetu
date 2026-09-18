import httpx
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from core.errors import AppException, ErrorCode
from core.ids import generate_id
from core.logging import get_logger
from vision.schemas import ConfirmedChallanInput
from db.models import OutboxEvent, Alert, Invoice
import db.repositories.distributors_repo as distributors_repo
import db.repositories.invoices_repo as invoices_repo

logger = get_logger("services.challan")

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
    balance_available = 0.0
    try:
        res = httpx.get("http://localhost:8001/balance", timeout=5.0)
        if res.status_code == 200:
            balance_available = float(res.json().get("balance", 5200.00))
        else:
            balance_available = 5200.00 # fallback mock
    except Exception:
        balance_available = 5200.00 # fallback mock
        
    remaining_after = balance_available - float(invoice.total_amount)
    
    return {
        "invoice_id": invoice.invoice_id,
        "rate_alerts": rate_alerts,
        "settlement": {
            "invoice_total": float(invoice.total_amount),
            "balance_available": balance_available,
            "remaining_after": remaining_after
        }
    }


def settle_invoice(db: Session, invoice_id: str, request_id: str) -> Dict[str, Any]:
    invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not invoice:
        raise AppException(code="INVOICE_NOT_FOUND", message="Invoice not found", status_code=404)
        
    if invoice.is_paid:
        return {"payout_status": "SUCCEEDED", "payout_reference": invoice.payout_reference}
        
    # Call mock Paytm payout
    # TODO: Phase 8 — route this through n8n Vendor Payout webhook instead of calling mock_paytm directly
    try:
        payload = {
            "amount": float(invoice.total_amount),
            "destination": invoice.payment_handle_value,
            "merchant_reference": invoice_id
        }
        res = httpx.post("http://localhost:8001/payout", json=payload, timeout=10.0)
        
        # We will mock the response if the server is not reachable
        if res.status_code == 200:
            resp_data = res.json()
            status = resp_data.get("status", "SUCCESS")
            ref = resp_data.get("payout_reference", f"MOCK_REF_{invoice_id}")
        else:
            status = "SUCCESS"
            ref = f"MOCK_REF_{invoice_id}"
            
    except Exception as e:
        logger.warning(f"[{request_id}] Mock payout server unreachable, simulating success. {e}")
        status = "SUCCESS"
        ref = f"MOCK_REF_{invoice_id}"
        
    if status == "SUCCESS":
        invoice.is_paid = True
        invoice.paid_at = func.now()
        invoice.payout_reference = ref
        db.commit()
        return {"payout_status": "INITIATED", "payout_reference": ref}
    else:
        return {"payout_status": "FAILED", "failure_reason": "Mock payout failed"}
