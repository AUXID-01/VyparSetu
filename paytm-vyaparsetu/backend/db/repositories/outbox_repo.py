from sqlalchemy.orm import Session
from db.models import OutboxEvent
from core.ids import generate_outbox_id

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
