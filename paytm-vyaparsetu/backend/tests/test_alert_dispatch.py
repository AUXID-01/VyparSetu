import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.session import SessionLocal
from db.models import Merchant, Alert
from core.ids import generate_id

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    db.query(Alert).filter_by(merchant_id="mer_alert_test").delete()
    db.query(Merchant).filter_by(merchant_id="mer_alert_test").delete()
    db.commit()

@pytest.fixture
def setup_data(db):
    merchant = Merchant(
        merchant_id="mer_alert_test",
        shop_name="Alert Test Shop",
        owner_name="Test Owner",
        phone="4444444444",
        cognee_dataset="ds_alert_test"
    )
    db.add(merchant)
    
    alert1 = Alert(
        alert_id="alrt_spike_test",
        merchant_id="mer_alert_test",
        alert_type="RATE_SPIKE",
        details={
            "sku": "Milk",
            "delta": 2.50
        }
    )
    db.add(alert1)
    
    alert2 = Alert(
        alert_id="alrt_payout_test",
        merchant_id="mer_alert_test",
        alert_type="PAYOUT_FAILED",
        details={
            "failure_reason": "Invalid Account"
        }
    )
    db.add(alert2)
    db.commit()
    
    return {"merchant_id": "mer_alert_test", "alert1": "alrt_spike_test", "alert2": "alrt_payout_test"}

def test_alert_dispatch_rate_spike(setup_data):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    payload = {"alert_id": setup_data["alert1"]}
    
    response = client.post("/api/v1/internal/alerts/dispatch-payload", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["alert_id"] == setup_data["alert1"]
    assert data["alert_type"] == "RATE_SPIKE"
    assert data["priority"] == "MEDIUM"
    assert "मूल्य वृद्धि चेतावनी" in data["message"]
    assert "Milk" in data["message"]
    assert "2.5" in data["message"]

def test_alert_dispatch_payout_failed(setup_data):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    payload = {"alert_id": setup_data["alert2"]}
    
    response = client.post("/api/v1/internal/alerts/dispatch-payload", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["alert_id"] == setup_data["alert2"]
    assert data["alert_type"] == "PAYOUT_FAILED"
    assert data["priority"] == "HIGH"
    assert "भुगतान विफल" in data["message"]
    assert "Invalid Account" in data["message"]

def test_alert_dispatch_unauthorized(setup_data):
    payload = {"alert_id": setup_data["alert1"]}
    response = client.post("/api/v1/internal/alerts/dispatch-payload", headers={"X-Internal-Token": "invalid"}, json=payload)
    assert response.status_code == 403
