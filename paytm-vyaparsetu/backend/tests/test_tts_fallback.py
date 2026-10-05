import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.session import SessionLocal
from db.models import LedgerTransaction
from services.voice_service import process_voice_credit_audio

@pytest.fixture(scope="function")
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_tts_failure_surfacing(db):
    from db.models import Merchant
    merchant_id = "test_tts_merchant"
    
    # Pre-create merchant to satisfy foreign key
    merchant = db.query(Merchant).filter_by(merchant_id=merchant_id).first()
    if not merchant:
        db.add(Merchant(merchant_id=merchant_id, shop_name="TTS Test", owner_name="TTS", phone="9999999988"))
        db.commit()
    
    audio_bytes = b"fake" * 1000
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract, \
         patch("services.voice_service.sarvam.synthesize_speech") as mock_tts:
             
        mock_stt.return_value = {"transcript": "500 rupaye added", "language_code": "hi-IN"}
        mock_extract.return_value = {"customer_name": "TTS Customer", "amount": 500.0, "confidence": 0.9}
        
        # Force TTS to fail
        mock_tts.side_effect = Exception("TTS synthesis timeout simulation")
        
        initial_ledgers = db.query(LedgerTransaction).filter_by(merchant_id=merchant_id).count()
        
        # Call the pipeline. It should NOT raise an exception.
        result = process_voice_credit_audio(db, merchant_id, audio_bytes, request_id="tts_test_req")
        
        # Assert A: Ledger write succeeded
        final_ledgers = db.query(LedgerTransaction).filter_by(merchant_id=merchant_id).count()
        assert final_ledgers == initial_ledgers + 1, "Ledger row was not written!"
        
        # Assert B: Response is populated correctly
        assert result["extracted"]["amount"] == 500.0
        assert result["extracted"]["customer_name"].lower() == "tts customer"
        assert result["confirmation_audio_text"] != ""
        
        # Assert C: Audio is null and status is UNAVAILABLE
        assert result["confirmation_audio_b64"] is None
        assert result["confirmation_audio_status"] == "UNAVAILABLE"
