import pytest
import sys
import os
import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.session import SessionLocal
from db.models import Invoice, Merchant, Distributor, OutboxEvent, Alert
from core.ids import generate_id

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    db.query(OutboxEvent).filter_by(merchant_id="mer_payout_test").delete()
    db.query(Alert).filter_by(merchant_id="mer_payout_test").delete()
    db.query(Invoice).filter_by(merchant_id="mer_payout_test").delete()
    db.query(Distributor).filter_by(merchant_id="mer_payout_test").delete()
    db.query(Merchant).filter_by(merchant_id="mer_payout_test").delete()
    db.commit()

@pytest.fixture
def setup_data(db):
    merchant = Merchant(
        merchant_id="mer_payout_test",
        shop_name="Payout Test Shop",
        owner_name="Test Owner",
        phone="7777777777",
        cognee_dataset="ds_payout_test"
    )
    db.add(merchant)
    
    distributor = Distributor(
        distributor_id="dist_payout_test",
        merchant_id="mer_payout_test",
        name="Test Dist",
        canonical_key="test_dist",
        upi_id="dist@upi"
    )
    db.add(distributor)
    
    invoice = Invoice(
        invoice_id="inv_payout_test",
        merchant_id="mer_payout_test",
        distributor_id="dist_payout_test",
        invoice_date=datetime.date.today(),
        total_amount=150.00,
        is_paid=False,
    )
    db.add(invoice)
    db.commit()
    
    return {"merchant_id": "mer_payout_test", "invoice_id": "inv_payout_test"}

def test_payout_callback_success(setup_data, db):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    payload = {
        "invoice_id": setup_data["invoice_id"],
        "merchant_id": setup_data["merchant_id"],
        "status": "SUCCESS",
        "utr_reference": "UTR123456"
    }
    
    response = client.post("/api/v1/internal/payout/callback", headers=headers, json=payload)
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert data["invoice_id"] == setup_data["invoice_id"]
    assert data["is_paid"] is True
    assert data["status"] == "SUCCESS"
    
    # Check DB
    invoice = db.query(Invoice).filter_by(invoice_id=setup_data["invoice_id"]).first()
    assert invoice.is_paid is True
    assert invoice.payout_reference == "UTR123456"
    
    # Check outbox event (ledger entry)
    outbox = db.query(OutboxEvent).filter_by(merchant_id=setup_data["merchant_id"], event_type="PAYOUT_SETTLED").first()
    assert outbox is not None
    assert outbox.payload["utr_reference"] == "UTR123456"
    assert outbox.payload["amount"] == 150.00


def test_payout_callback_failed(setup_data, db):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    payload = {
        "invoice_id": setup_data["invoice_id"],
        "merchant_id": setup_data["merchant_id"],
        "status": "FAILED",
        "failure_reason": "Bank declined"
    }
    
    response = client.post("/api/v1/internal/payout/callback", headers=headers, json=payload)
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert data["is_paid"] is False
    assert data["status"] == "FAILED"
    
    # Check DB
    invoice = db.query(Invoice).filter_by(invoice_id=setup_data["invoice_id"]).first()
    assert invoice.is_paid is False
    
    # Check Alert
    alert = db.query(Alert).filter_by(merchant_id=setup_data["merchant_id"], alert_type="PAYOUT_FAILED").first()
    assert alert is not None
    assert alert.details["failure_reason"] == "Bank declined"


def test_payout_callback_unauthorized(setup_data):
    payload = {
        "invoice_id": setup_data["invoice_id"],
        "merchant_id": setup_data["merchant_id"],
        "status": "SUCCESS"
    }
    response = client.post("/api/v1/internal/payout/callback", headers={"X-Internal-Token": "invalid"}, json=payload)
    assert response.status_code == 403
