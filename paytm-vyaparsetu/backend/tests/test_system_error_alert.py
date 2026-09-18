import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.session import SessionLocal
from db.models import Merchant, Alert

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    # Just clean alerts created for SYSTEM to prevent build up
    db.query(Alert).filter_by(merchant_id="SYSTEM").delete()
    db.query(Merchant).filter_by(merchant_id="SYSTEM").delete()
    db.commit()

def test_system_error_alert_success(db):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    payload = {
        "workflow_name": "Test Workflow",
        "execution_id": "exec_12345",
        "error_message": "Node timeout",
        "node_name": "HTTP Request",
        "details": {"retry": 3}
    }
    
    response = client.post("/api/v1/internal/alerts/system-error", headers=headers, json=payload)
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert "alert_id" in data
    assert data["status"] == "LOGGED"
    
    # Check DB
    alert = db.query(Alert).filter_by(alert_id=data["alert_id"]).first()
    assert alert is not None
    assert alert.merchant_id == "SYSTEM"
    assert alert.alert_type == "SYSTEM_ERROR"
    assert alert.details["workflow"] == "Test Workflow"
    assert alert.details["execution_id"] == "exec_12345"
    assert alert.details["node"] == "HTTP Request"
    assert alert.details["error"] == "Node timeout"
    assert alert.details["extra"] == {"retry": 3}
    assert alert.is_read is False

def test_system_error_alert_unauthorized():
    payload = {
        "workflow_name": "Test Workflow",
        "execution_id": "exec_12345",
        "error_message": "Node timeout"
    }
    response = client.post("/api/v1/internal/alerts/system-error", headers={"X-Internal-Token": "invalid"}, json=payload)
    assert response.status_code == 403
