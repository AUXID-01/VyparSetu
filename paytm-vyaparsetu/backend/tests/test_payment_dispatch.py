import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.session import SessionLocal
from db.models import Customer, Merchant

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    db.query(Customer).filter_by(customer_id="cust_pay_test").delete()
    db.query(Merchant).filter_by(merchant_id="mer_payment_test").delete()
    db.commit()

@pytest.fixture
def setup_data(db):
    merchant = Merchant(
        merchant_id="mer_payment_test",
        shop_name="Pay Test Shop",
        owner_name="Test Owner",
        phone="1111111111",
        cognee_dataset="ds_pay_test"
    )
    db.add(merchant)
    db.commit()
    
    customer = Customer(
        customer_id="cust_pay_test",
        merchant_id="mer_payment_test",
        display_name="Ravi Kumar",
        canonical_key="ravi_kumar_9876543210",
        phone="9876543210"
    )
    db.add(customer)
    db.commit()
    return {"merchant_id": "mer_payment_test", "customer_id": "cust_pay_test"}

def test_payment_dispatch_unauthorized():
    payload = {
        "merchant_id": "mer_payment_test",
        "customer_id": "cust_pay_test",
        "amount": 55.50
    }
    response = client.post("/api/v1/internal/notifications/payment-link", headers={"X-Internal-Token": "invalid"}, json=payload)
    assert response.status_code == 403

def test_payment_dispatch_authorized(setup_data):
    headers = {"X-Internal-Token": settings.INTERNAL_TOKEN}
    payload = {
        "merchant_id": setup_data["merchant_id"],
        "customer_id": setup_data["customer_id"],
        "amount": 55.50
    }
    
    response = client.post("/api/v1/internal/notifications/payment-link", headers=headers, json=payload)
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert data["phone"] == "9876543210"
    assert data["customer_name"] == "Ravi Kumar"
    assert data["merchant_name"] == "Pay Test Shop"
    assert data["amount"] == 55.50
    assert "https://paytm.me/mock-" in data["payment_url"]
    assert "नमस्ते Ravi Kumar, Pay Test Shop पर आपका ₹55.50 का उधार दर्ज हुआ है" in data["message"]
