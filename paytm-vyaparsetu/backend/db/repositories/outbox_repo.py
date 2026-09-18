from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from db.models import OutboxEvent
from core.ids import generate_outbox_id
from core.logging import get_logger

logger = get_logger("db.outbox_repo")

def create_event(
    db: Session,
    merchant_id: str,
    event_type: str,
    payload: dict
) -> OutboxEvent:
    event = OutboxEvent(
        event_id=generate_outbox_id(),
        merchant_id=merchant_id,
        event_type=event_type,
        payload=payload,
        status="PENDING"
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

create_outbox_event = create_event

def get_pending_events(db: Session, limit: int = 50) -> List[OutboxEvent]:
    events = db.query(OutboxEvent).filter(
        OutboxEvent.status == "PENDING"
    ).order_by(OutboxEvent.created_at.asc()).limit(limit).all()
    logger.info(f"🔍 [DB Read] Fetched {len(events)} PENDING outbox events (limit {limit})")
    return events

def mark_event_synced(db: Session, event_id: str) -> Optional[OutboxEvent]:
    event = db.query(OutboxEvent).filter(OutboxEvent.event_id == event_id).first()
    if not event:
        return None
    event.status = "SYNCED"
    event.synced_at = func.now()
    db.commit()
    db.refresh(event)
    logger.info(f"💾 [DB Write] Marked event {event_id} as SYNCED")
    return event

def mark_event_failed(db: Session, event_id: str) -> Optional[OutboxEvent]:
    event = db.query(OutboxEvent).filter(OutboxEvent.event_id == event_id).first()
    if not event:
        return None
    event.attempt_count += 1
    if event.attempt_count >= 5:
        event.status = "FAILED"
        logger.info(f"💾 [DB Write] Marked event {event_id} as FAILED (attempts >= 5)")
    else:
        logger.info(f"💾 [DB Write] Incremented attempt count for event {event_id} to {event.attempt_count}")
    db.commit()
    db.refresh(event)
    return event
