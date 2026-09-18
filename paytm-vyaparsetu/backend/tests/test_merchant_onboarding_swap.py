import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.session import SessionLocal
from db.models import Merchant

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    db.query(Merchant).filter_by(merchant_id="mer_onboarding_test").delete()
    db.commit()

@pytest.fixture
def setup_data(db):
    merchant = Merchant(
        merchant_id="mer_onboarding_test",
        shop_name="Welcome Shop",
        owner_name="New Owner",
        phone="5555555555",
        cognee_dataset="ds_pending_onboard"
    )
    db.add(merchant)
    db.commit()
    return {"merchant_id": "mer_onboarding_test"}

def test_provision_dataset_success(setup_data):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    payload = {"merchant_id": setup_data["merchant_id"]}
    
    response = client.post("/api/v1/internal/merchants/provision-dataset", headers=headers, json=payload)
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert data["merchant_id"] == setup_data["merchant_id"]
    assert data["owner_name"] == "New Owner"
    assert data["shop_name"] == "Welcome Shop"
    assert data["status"] == "PROVISIONED"
    assert "नमस्ते New Owner! Paytm VyaparSetu में आपका स्वागत है।" in data["welcome_message"]
    # get_dataset_for_merchant sets dataset
    assert data["dataset_name"] is not None

def test_provision_dataset_unauthorized(setup_data):
    payload = {"merchant_id": setup_data["merchant_id"]}
    response = client.post("/api/v1/internal/merchants/provision-dataset", headers={"X-Internal-Token": "invalid"}, json=payload)
    assert response.status_code == 403
