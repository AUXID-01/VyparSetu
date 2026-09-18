import sys
import os
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db.session import SessionLocal
from db.models import Merchant, Distributor, Invoice, InvoiceLineItem, Alert, OutboxEvent, InvoiceExtractionAudit
from core.ids import generate_id
from datetime import datetime, timedelta

client = TestClient(app)

def seed_historical_invoice(db: Session, merchant_id: str, distributor_name: str, sku: str, old_price: float):
    # Ensure merchant exists
    merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
    if not merchant:
        merchant = Merchant(
            merchant_id=merchant_id,
            shop_name="E2E Shop",
            owner_name="Test Owner",
            phone="9998887776",
            cognee_dataset="ds_test"
        )
        db.add(merchant)

    canonical_key = distributor_name.strip().lower()
    distributor = db.query(Distributor).filter(Distributor.merchant_id == merchant_id, Distributor.canonical_key == canonical_key).first()
    if not distributor:
        distributor = Distributor(
            distributor_id=generate_id("dis_"),
            merchant_id=merchant_id,
            name=distributor_name,
            canonical_key=canonical_key
        )
        db.add(distributor)
        
    db.flush()

    invoice_id = generate_id("inv_")
    old_invoice = Invoice(
        invoice_id=invoice_id,
        merchant_id=merchant_id,
        distributor_id=distributor.distributor_id,
        invoice_date=(datetime.utcnow() - timedelta(days=5)).date(),
        total_amount=old_price,
        is_paid=True
    )
    db.add(old_invoice)

    line_item = InvoiceLineItem(
        line_item_id=generate_id("lin_"),
        invoice_id=invoice_id,
        distributor_id=distributor.distributor_id,
        sku=sku,
        quantity=1.0,
        unit_price=old_price
    )
    db.add(line_item)
    db.commit()

def run_e2e():
    print("Starting E2E verification...")
    db = SessionLocal()
    merchant_id = "mer_e2e_test_01"
    
    unique_suffix = generate_id("")
    sku_name = f"Electric Drill Machine {unique_suffix}"
    
    # 1. Seed historical data
    print("Seeding historical invoice...")
    seed_historical_invoice(db, merchant_id, "Gujarat Freight Tools", sku_name, 450.00)

    # 2. Call /confirm with increased price
    print("Calling POST /api/v1/challan/confirm...")
    confirm_payload = {
        "merchant_id": merchant_id,
        "data": {
            "challan_type": "FORMAL_GST",
            "capture_medium": "CAMERA_PHOTO",
            "distributor_name_raw": "Gujarat Freight Tools",
            "subtotal": 487.29,
            "total_payable": 487.29,
            "line_items": [
                {
                    "raw_text": "1x Drill",
                    "canonical_item_name": sku_name,
                    "quantity": 1.0,
                    "unit": "pcs",
                    "unit_rate": 487.29,
                    "line_total": 487.29,
                    "is_free_scheme": False,
                    "item_confidence": 0.99
                }
            ],
            "packaging_adjustments": [],
            "tax": {"cgst": 0.0, "sgst": 0.0},
            "ocr_raw_text": "Test OCR text",
            "vision_llm_raw_response": {"fake": "json"}
        }
    }

    res_confirm = client.post("/api/v1/challan/confirm", json=confirm_payload)
    assert res_confirm.status_code == 200, f"Confirm failed: {res_confirm.text}"
    
    confirm_data = res_confirm.json()["data"]
    invoice_id = confirm_data["invoice_id"]
    rate_alerts = confirm_data["rate_alerts"]
    
    print(f"Invoice created: {invoice_id}")
    print(f"Rate Alerts returned: {rate_alerts}")
    
    # Debug: print all line items
    all_items = db.query(InvoiceLineItem).filter(InvoiceLineItem.sku == "Electric Drill Machine").all()
    for item in all_items:
        print(f"DB Item: id={item.line_item_id} inv={item.invoice_id} sku={item.sku} price={item.unit_price}")
    
    # Verify Rate Alert
    assert len(rate_alerts) == 1, "Expected exactly 1 rate alert"
    assert round(rate_alerts[0]["delta"], 2) == 37.29, "Expected rate spike delta of 37.29"

    # Verify DB state
    db.expire_all()
    invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    assert invoice is not None, "Invoice not saved to DB"
    assert invoice.is_paid == False, "New invoice should be unpaid"

    audit = db.query(InvoiceExtractionAudit).filter(InvoiceExtractionAudit.invoice_id == invoice_id).first()
    assert audit is not None, "Extraction audit not saved"
    assert audit.ocr_raw_text == "Test OCR text"

    outbox = db.query(OutboxEvent).filter(OutboxEvent.merchant_id == merchant_id, OutboxEvent.status == "PENDING").order_by(OutboxEvent.created_at.desc()).first()
    assert outbox is not None, "Outbox event not queued"
    assert outbox.event_type == "INVOICE_CREATED"
    
    db_alert = db.query(Alert).filter(Alert.merchant_id == merchant_id, Alert.alert_type == "RATE_SPIKE").order_by(Alert.created_at.desc()).first()
    assert db_alert is not None, "Rate spike alert not saved to DB"
    assert round(db_alert.details["delta"], 2) == 37.29
    
    # 3. Call /settle
    print(f"Calling POST /api/v1/challan/settle for {invoice_id}...")
    settle_payload = {"invoice_id": invoice_id}
    res_settle = client.post("/api/v1/challan/settle", json=settle_payload)
    assert res_settle.status_code == 200, f"Settle failed: {res_settle.text}"
    
    settle_data = res_settle.json()["data"]
    print(f"Settle response: {settle_data}")
    assert settle_data["payout_status"] == "INITIATED"
    
    # Verify DB transition
    db.expire_all()
    settled_invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    assert settled_invoice.is_paid == True, "Invoice was not marked as paid"
    assert settled_invoice.payout_reference is not None, "Payout reference missing"

    print("\n✅ Verification Successful: All Step 3 wiring requirements satisfied!")
    
if __name__ == "__main__":
    run_e2e()
