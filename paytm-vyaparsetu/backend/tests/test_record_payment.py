import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app
from db.session import SessionLocal
from db.models import Merchant, Customer, LedgerTransaction, OutboxEvent
from core.enums import TxnType, OutboxEventType, OutboxStatus
from core.ids import generate_id

client = TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def setup_test_data(db):
    import random
    merchant_id = generate_id("mer_")
    random_phone = str(random.randint(1000000000, 9999999999))
    merchant = Merchant(
        merchant_id=merchant_id,
        shop_name="Test Shop",
        owner_name="Test Owner",
        phone=random_phone,
        cognee_dataset=f"merchant_{merchant_id}"
    )
    db.add(merchant)
    
    customer_id = generate_id("cus_")
    customer = Customer(
        customer_id=customer_id,
        merchant_id=merchant_id,
        display_name="Test Customer",
        canonical_key="test_customer"
    )
    db.add(customer)
    
    # Add initial debt
    txn = LedgerTransaction(
        txn_id=generate_id("txn_"),
        merchant_id=merchant_id,
        customer_id=customer_id,
        amount=1000.0,
        txn_type=TxnType.CREDIT_ADDED.value,
        source="MANUAL",
        items=[]
    )
    db.add(txn)
    db.commit()
    
    return {"merchant_id": merchant_id, "customer_id": customer_id}

def test_record_payment_success(db, setup_test_data):
    merchant_id = setup_test_data["merchant_id"]
    customer_id = setup_test_data["customer_id"]
    
    payload = {
        "customer_id": customer_id,
        "amount": 400.0,
        "source": "CASH"
    }
    
    headers = {"Authorization": f"Bearer {merchant_id}"}
    response = client.post("/api/v1/ledger/record-payment", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["amount"] == 400.0
    
    # Verify Ledger
    txns = db.query(LedgerTransaction).filter(LedgerTransaction.customer_id == customer_id).all()
    assert len(txns) == 2
    payment_txn = [t for t in txns if t.txn_type == TxnType.CREDIT_PAID.value][0]
    assert payment_txn.amount == 400.0
    
    # Verify Outbox
    outbox = db.query(OutboxEvent).filter(
        OutboxEvent.event_type == OutboxEventType.CUSTOMER_PAYMENT_SETTLED.value,
        OutboxEvent.merchant_id == merchant_id
    ).first()
    assert outbox is not None
    assert outbox.payload["amount"] == 400.0
    assert outbox.status == OutboxStatus.PENDING.value

def test_mock_webhook_success(db, setup_test_data):
    merchant_id = setup_test_data["merchant_id"]
    customer_id = setup_test_data["customer_id"]
    
    payload = {
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "amount": 250.0,
        "payment_reference": "UPI12345",
        "status": "SUCCESS"
    }
    
    response = client.post("/api/v1/payments/mock-webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify Ledger
    payment_txn = db.query(LedgerTransaction).filter(
        LedgerTransaction.customer_id == customer_id,
        LedgerTransaction.txn_type == TxnType.CREDIT_PAID.value,
        LedgerTransaction.amount == 250.0
    ).first()
    assert payment_txn is not None
