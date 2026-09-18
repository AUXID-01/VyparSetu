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
