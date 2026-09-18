import pytest
import sys
import os
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
def sample_event(db):
    merchant_id = "mer_test_outbox"
    merchant = db.query(Merchant).filter_by(merchant_id=merchant_id).first()
    if not merchant:
        merchant = Merchant(
            merchant_id=merchant_id,
            shop_name="Outbox Test Shop",
            owner_name="Test Owner",
            phone="9999999999",
            cognee_dataset="ds_test"
        )
        db.add(merchant)
        db.commit()

    event = OutboxEvent(
        event_id=generate_outbox_id(),
        merchant_id=merchant_id,
        event_type="TEST_EVENT",
        payload={"foo": "bar"},
        status="PENDING"
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def test_pending_outbox_unauthorized():
    headers = {"X-Internal-Token": "wrong_token_here"}
    response = client.get("/api/v1/internal/outbox/pending", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INTERNAL_TOKEN_INVALID"

def test_pending_outbox_authorized(sample_event):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    response = client.get("/api/v1/internal/outbox/pending", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["event_id"] == sample_event.event_id
    assert "status" not in data[0] # We don't expose status in the payload

def test_outbox_callback_synced(db, sample_event):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    payload = {
        "event_id": sample_event.event_id,
        "status": "SYNCED"
    }
    response = client.post("/api/v1/internal/outbox/callback", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["event_id"] == sample_event.event_id
    assert data["status"] == "SYNCED"
    
    # Verify in DB
    db.refresh(sample_event)
    assert sample_event.status == "SYNCED"
    assert sample_event.synced_at is not None

def test_outbox_callback_idempotent(db, sample_event):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    payload = {
        "event_id": sample_event.event_id,
        "status": "SYNCED"
    }
    
    # First call
    response1 = client.post("/api/v1/internal/outbox/callback", headers=headers, json=payload)
    assert response1.status_code == 200
    
    # Second call (idempotent)
    response2 = client.post("/api/v1/internal/outbox/callback", headers=headers, json=payload)
    assert response2.status_code == 200
    
    # Should still be SYNCED
    db.refresh(sample_event)
    assert sample_event.status == "SYNCED"
