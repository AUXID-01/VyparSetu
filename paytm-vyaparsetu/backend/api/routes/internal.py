from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from api.deps import get_db, verify_internal_token
from core.errors import success_envelope, AppException, ErrorCode
from core.logging import get_logger
import db.repositories.outbox_repo as outbox_repo
import memory
from services import payment_service

logger = get_logger("api.routes.internal")

router = APIRouter(dependencies=[Depends(verify_internal_token)])

class PaymentLinkRequest(BaseModel):
    merchant_id: str
    customer_id: str
    amount: float

class PayoutCallbackRequest(BaseModel):
    invoice_id: str
    merchant_id: str
    status: str
    utr_reference: Optional[str] = None
    failure_reason: Optional[str] = None

class AlertDispatchRequest(BaseModel):
    alert_id: str

class SystemErrorAlertRequest(BaseModel):
    workflow_name: str
    execution_id: str
    error_message: str
    node_name: Optional[str] = None
    details: Optional[dict] = None

class ProvisionDatasetRequest(BaseModel):
    merchant_id: str

class MemorySyncRequest(BaseModel):
    event_id: str
    merchant_id: str
    event_type: str
    payload: dict

class OutboxCallbackPayload(BaseModel):
    event_id: str
    status: str

@router.get("/outbox/pending")
def get_pending_outbox_events(request: Request, limit: int = 20, db: Session = Depends(get_db)):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] GET /internal/outbox/pending ingress (limit={limit})")
    
    events = outbox_repo.get_pending_events(db, limit=limit)
    data = [
        {
            "event_id": e.event_id,
            "merchant_id": e.merchant_id,
            "event_type": e.event_type,
            "payload": e.payload,
            "created_at": e.created_at.isoformat() if e.created_at else None
        } for e in events
    ]
    
    logger.info(f"📤 [{req_id}] [JSON Payload] GET /internal/outbox/pending egress (count={len(data)})")
    return success_envelope(data)

@router.get("/outbox/stuck")
def get_stuck_pending_events(request: Request, age_minutes: int = 5, limit: int = 20, db: Session = Depends(get_db)):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] GET /internal/outbox/stuck ingress (age_minutes={age_minutes}, limit={limit})")
    
    events = outbox_repo.get_stuck_pending_events(db, age_minutes=age_minutes, limit=limit)
    data = [
        {
            "event_id": e.event_id,
            "merchant_id": e.merchant_id,
            "event_type": e.event_type,
            "payload": e.payload,
            "attempt_count": e.attempt_count,
            "created_at": e.created_at.isoformat() if e.created_at else None
        } for e in events
    ]
    
    logger.info(f"📤 [{req_id}] [JSON Payload] GET /internal/outbox/stuck egress (count={len(data)})")
    return success_envelope(data)


@router.post("/outbox/callback")
def outbox_callback(
    request: Request,
    payload: OutboxCallbackPayload,
    db: Session = Depends(get_db)
):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] POST /internal/outbox/callback ingress: {payload.model_dump()}")
    
    if payload.status not in ("SYNCED", "FAILED"):
        raise AppException(
            code="INVALID_REQUEST", 
            message="Status must be SYNCED or FAILED", 
            status_code=400
        )
        
    if payload.status == "SYNCED":
        updated = outbox_repo.mark_event_synced(db, payload.event_id)
    else:
        updated = outbox_repo.mark_event_failed(db, payload.event_id)
        
    if not updated:
        raise AppException(
            code="NOT_FOUND", 
            message=f"Event {payload.event_id} not found", 
            status_code=404
        )
        
    result_data = {"event_id": updated.event_id, "status": updated.status}
    logger.info(f"📤 [{req_id}] [JSON Payload] POST /internal/outbox/callback egress: {result_data}")
    return success_envelope(result_data)

@router.post("/memory/sync")
async def memory_sync(
    request: Request,
    payload: MemorySyncRequest,
    db: Session = Depends(get_db)
):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] POST /internal/memory/sync ingress: {payload.model_dump()}")
    
    dataset_name = memory.get_dataset_for_merchant(db, payload.merchant_id)
    
    if payload.event_type == "CREDIT_ADDED":
        await memory.remember_transaction(dataset_name, payload.payload)
    elif payload.event_type == "INVOICE_CREATED":
        await memory.remember_invoice(dataset_name, payload.payload)
    else:
        logger.warning(f"Unhandled event_type: {payload.event_type}")
        
    await memory.cognify_dataset(dataset_name)
    
    result_data = {"event_id": payload.event_id, "status": "COGNIFIED"}
    logger.info(f"📤 [{req_id}] [JSON Payload] POST /internal/memory/sync egress: {result_data}")
    return success_envelope(result_data)

@router.post("/notifications/payment-link")
def dispatch_payment_link(
    request: Request,
    payload: PaymentLinkRequest,
    db: Session = Depends(get_db)
):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] POST /internal/notifications/payment-link ingress: {payload.model_dump()}")
    
    link_payload = payment_service.generate_payment_link_payload(
        db, payload.merchant_id, payload.customer_id, payload.amount
    )
    
    logger.info(f"📤 [{req_id}] [JSON Payload] POST /internal/notifications/payment-link egress: {link_payload}")
    return success_envelope(link_payload)

@router.post("/payout/callback")
def payout_callback(
    request: Request,
    payload: PayoutCallbackRequest,
    db: Session = Depends(get_db)
):
    from db.models import Invoice, Alert, OutboxEvent
    from core.ids import generate_id
    from sqlalchemy.sql import func
    
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] POST /internal/payout/callback ingress: {payload.model_dump()}")
    
    invoice = db.query(Invoice).filter(
        Invoice.invoice_id == payload.invoice_id,
        Invoice.merchant_id == payload.merchant_id
    ).first()
    
    if not invoice:
        raise AppException(
            code="INVOICE_NOT_FOUND",
            message=f"Invoice {payload.invoice_id} not found",
            status_code=404
        )
        
    if payload.status == "SUCCESS":
        invoice.is_paid = True
        invoice.paid_at = func.now()
        invoice.payout_reference = payload.utr_reference
        
        # Log ledger entry for vendor settlement payout in outbox
        outbox_id = generate_id("out_")
        outbox = OutboxEvent(
            event_id=outbox_id,
            merchant_id=payload.merchant_id,
            event_type="PAYOUT_SETTLED",
            payload={
                "invoice_id": invoice.invoice_id,
                "amount": float(invoice.total_amount),
                "utr_reference": payload.utr_reference
            },
            status="PENDING"
        )
        db.add(outbox)
        
    elif payload.status == "FAILED":
        invoice.is_paid = False
        
        alert_id = generate_id("alrt_")
        alert = Alert(
            alert_id=alert_id,
            merchant_id=payload.merchant_id,
            alert_type="PAYOUT_FAILED",
            details={
                "invoice_id": invoice.invoice_id,
                "amount": float(invoice.total_amount),
                "failure_reason": payload.failure_reason
            }
        )
        db.add(alert)
        
    else:
        raise AppException(
            code="INVALID_STATUS",
            message="Status must be SUCCESS or FAILED",
            status_code=400
        )
        
    db.commit()
    
    result_data = {
        "invoice_id": invoice.invoice_id,
        "is_paid": invoice.is_paid,
        "status": payload.status
    }
    
    logger.info(f"📤 [{req_id}] [JSON Payload] POST /internal/payout/callback egress: {result_data}")
    return success_envelope(result_data)

@router.post("/alerts/dispatch-payload")
def dispatch_alert_payload(
    request: Request,
    payload: AlertDispatchRequest,
    db: Session = Depends(get_db)
):
    from services import alert_service
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] POST /internal/alerts/dispatch-payload ingress: {payload.model_dump()}")
    
    dispatch_data = alert_service.format_alert_dispatch_payload(db, payload.alert_id)
    
    logger.info(f"📤 [{req_id}] [JSON Payload] POST /internal/alerts/dispatch-payload egress: {dispatch_data}")
    return success_envelope(dispatch_data)

@router.post("/merchants/provision-dataset")
def provision_merchant_dataset(
    request: Request,
    payload: ProvisionDatasetRequest,
    db: Session = Depends(get_db)
):
    from db.models import Merchant
    from memory.dataset_manager import get_dataset_for_merchant
    
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] POST /internal/merchants/provision-dataset ingress: {payload.model_dump()}")
    
    merchant = db.query(Merchant).filter(Merchant.merchant_id == payload.merchant_id).first()
    if not merchant:
        raise AppException(
            code="MERCHANT_NOT_FOUND",
            message=f"Merchant {payload.merchant_id} not found",
            status_code=404
        )
        
    dataset_name = get_dataset_for_merchant(db, payload.merchant_id)
    
    welcome_message = f"नमस्ते {merchant.owner_name}! Paytm VyaparSetu में आपका स्वागत है। {merchant.shop_name} के लिए आपका स्मार्ट खाता और AI बहीखाता तैयार है।"
    
    result_data = {
        "merchant_id": payload.merchant_id,
        "dataset_name": dataset_name,
        "owner_name": merchant.owner_name,
        "shop_name": merchant.shop_name,
        "phone": merchant.phone,
        "welcome_message": welcome_message,
        "status": "PROVISIONED"
    }
    
    logger.info(f"📤 [{req_id}] [JSON Payload] POST /internal/merchants/provision-dataset egress: {result_data}")
    return success_envelope(result_data)


@router.post("/alerts/system-error")
def log_system_error(
    request: Request,
    payload: SystemErrorAlertRequest,
    db: Session = Depends(get_db)
):
    from db.models import Merchant, Alert
    from core.ids import generate_id
    
    req_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"📥 [{req_id}] [JSON Payload] POST /internal/alerts/system-error ingress: {payload.model_dump()}")
    
    # Ensure "SYSTEM" merchant exists for foreign key constraint
    system_merchant = db.query(Merchant).filter(Merchant.merchant_id == "SYSTEM").first()
    if not system_merchant:
        system_merchant = Merchant(
            merchant_id="SYSTEM",
            shop_name="VyaparSetu System",
            owner_name="System",
            phone="0000000000",
            cognee_dataset="system_metrics"
        )
        db.add(system_merchant)
        db.flush()
        
    alert_id = generate_id("alrt_")
    
    alert = Alert(
        alert_id=alert_id,
        merchant_id="SYSTEM",
        alert_type="SYSTEM_ERROR",
        details={
            "workflow": payload.workflow_name,
            "execution_id": payload.execution_id,
            "node": payload.node_name,
            "error": payload.error_message,
            "extra": payload.details
        },
        is_read=False
    )
    db.add(alert)
    db.commit()
    
    logger.info(f"🚨 [System Error] Logged workflow failure from {payload.workflow_name} ({payload.execution_id})")
    
    result_data = {
        "alert_id": alert_id,
        "status": "LOGGED"
    }
    
    logger.info(f"📤 [{req_id}] [JSON Payload] POST /internal/alerts/system-error egress: {result_data}")
    return success_envelope(result_data)




