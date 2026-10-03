import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.session import SessionLocal
from db.models import OutboxEvent, LedgerTransaction, Invoice
from services.voice_service import process_voice_credit_audio
from services.challan_service import confirm_challan

@pytest.fixture(scope="function")
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_voice_pipeline_atomic_rollback(db):
    merchant_id = "test_atomic_voice"
    audio_bytes = b"fake" * 1000
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract, \
         patch("services.voice_service.outbox_repo.create_outbox_event") as mock_outbox:
             
        mock_stt.return_value = {"transcript": "valid text", "language_code": "hi-IN"}
        mock_extract.return_value = {"customer_name": "Atomic Customer", "amount": 100.0, "confidence": 0.9}
        
        # Force outbox to fail AFTER ledger insert
        mock_outbox.side_effect = Exception("Outbox failure simulation")
        
        # Check initial counts
        initial_ledgers = db.query(LedgerTransaction).filter_by(merchant_id=merchant_id).count()
        initial_outbox = db.query(OutboxEvent).filter_by(merchant_id=merchant_id).count()
        
        with pytest.raises(Exception):
            process_voice_credit_audio(db, merchant_id, audio_bytes)
            
        # Verify atomicity
        final_ledgers = db.query(LedgerTransaction).filter_by(merchant_id=merchant_id).count()
        final_outbox = db.query(OutboxEvent).filter_by(merchant_id=merchant_id).count()
        
        assert final_ledgers == initial_ledgers, "Ledger row was persisted despite failure!"
        assert final_outbox == initial_outbox, "Outbox row was persisted despite failure!"

def test_challan_pipeline_atomic_rollback(db):
    merchant_id = "test_atomic_challan"
    payload = {
        "distributor_name_raw": "Atomic Dist",
        "total_payable": 500.0,
        "line_items": [{"item_name_raw": "Item 1", "quantity": 10, "unit_price": 50}],
        "packaging_adjustments": []
    }
    
    with patch("services.challan_service.invoices_repo.insert_line_items") as mock_line_items:
        # Force failure AFTER invoice row is added
        mock_line_items.side_effect = Exception("Line items failure simulation")
        
        initial_invoices = db.query(Invoice).filter_by(merchant_id=merchant_id).count()
        
        with pytest.raises(Exception):
            confirm_challan(db, merchant_id, payload, "test_req")
            
        final_invoices = db.query(Invoice).filter_by(merchant_id=merchant_id).count()
        
        assert final_invoices == initial_invoices, "Invoice row was persisted despite failure!"
