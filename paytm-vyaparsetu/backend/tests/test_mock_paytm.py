from fastapi.testclient import TestClient
from mock_services.mock_paytm.main import app as mock_paytm_app

client = TestClient(mock_paytm_app)

def test_mock_paytm_balance():
    response = client.get("/balance")
    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == 5200.00
    assert data["currency"] == "INR"

def test_mock_paytm_payout_success():
    payload = {
        "invoice_id": "inv_test123",
        "distributor_upi_id": "amul@paytm",
        "amount": 3850.00
    }
    response = client.post("/payout", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["payout_reference"].startswith("PAYTM-MOCK-")
    assert data["failure_reason"] is None

def test_mock_paytm_payout_insufficient_funds():
    payload = {
        "invoice_id": "inv_test456",
        "distributor_upi_id": "amul@paytm",
        "amount": 15000.00
    }
    response = client.post("/payout", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["payout_reference"] is None
    assert data["failure_reason"] == "INSUFFICIENT_FUNDS"
