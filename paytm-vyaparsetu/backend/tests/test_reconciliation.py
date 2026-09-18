import pytest
import sys
import os
import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.session import SessionLocal
from db.models import OutboxEvent, Merchant
from core.ids import generate_outbox_id

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    db.query(OutboxEvent).delete()
    db.commit()

@pytest.fixture
def merchant(db):
    merchant_id = "mer_reconciliation_test"
    merchant = db.query(Merchant).filter_by(merchant_id=merchant_id).first()
    if not merchant:
        merchant = Merchant(
            merchant_id=merchant_id,
            shop_name="Recon Test Shop",
            owner_name="Test Owner",
            phone="8888888888",
            cognee_dataset="ds_test"
        )
        db.add(merchant)
        db.commit()
    return merchant

def test_stuck_pending_events(db, merchant):
    # Insert 10-minute old event
    old_event = OutboxEvent(
        event_id=generate_outbox_id(),
        merchant_id=merchant.merchant_id,
        event_type="TEST_OLD",
        payload={"age": "old"},
        status="PENDING"
    )
    db.add(old_event)
    db.commit()
    
    # Overwrite created_at directly
    old_event.created_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
    db.commit()

    # Insert new event (<1 minute old)
    new_event = OutboxEvent(
        event_id=generate_outbox_id(),
        merchant_id=merchant.merchant_id,
        event_type="TEST_NEW",
        payload={"age": "new"},
        status="PENDING"
    )
    db.add(new_event)
    db.commit()

    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    response = client.get("/api/v1/internal/outbox/stuck?age_minutes=5", headers=headers)
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["event_id"] == old_event.event_id
    assert data[0]["event_type"] == "TEST_OLD"
