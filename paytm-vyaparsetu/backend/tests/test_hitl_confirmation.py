import pytest
import sys
import os
import json
import base64
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from db.session import SessionLocal, engine
from api.deps import get_db
from db.models import LedgerTransaction
from sqlalchemy.orm import sessionmaker
import sqlalchemy
from config import settings

client = TestClient(app)

@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()
    
    nested = connection.begin_nested()
    
    @sqlalchemy.event.listens_for(session, "after_transaction_end")
    def end_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()
    
    def override_get_db():
        try:
            yield session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()

def _check_real_count(merchant_id: str) -> int:
    isolated_db = SessionLocal()
    try:
        return isolated_db.query(LedgerTransaction).filter_by(merchant_id=merchant_id).count()
    finally:
        isolated_db.close()

def test_hitl_1_high_confidence_confirmed(db):
    mer = "mer_gupta01"
    audio_content = b"fakeaudio" * 200
    initial_count = db.query(LedgerTransaction).filter_by(merchant_id=mer).count()
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract, \
         patch("services.voice_service.sarvam.synthesize_speech") as mock_tts:
             
        mock_stt.return_value = {"transcript": "500 added", "language_code": "hi-IN"}
        mock_extract.return_value = {"customer_name": "Suresh", "amount": 500.0, "confidence": 0.80} # >= 0.75
        mock_tts.return_value = b"faketts"
        
        response = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        )
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["data"]["outcome"] == "CONFIRMED"
        assert db.query(LedgerTransaction).filter_by(merchant_id=mer).count() == initial_count + 1

def test_hitl_2_medium_confidence_needs_confirmation(db):
    mer = "mer_gupta01"
    audio_content = b"fakeaudio" * 200
    initial_count = db.query(LedgerTransaction).filter_by(merchant_id=mer).count()
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract:
             
        mock_stt.return_value = {"transcript": "500 added maybe", "language_code": "hi-IN"}
        mock_extract.return_value = {"customer_name": "Suresh", "amount": 500.0, "confidence": 0.60} # [0.40, 0.75)
        
        response = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        )
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["data"]["outcome"] == "NEEDS_CONFIRMATION"
        assert "confirmation_token" in res_data["data"]
        
        # Verify nothing written yet
        assert db.query(LedgerTransaction).filter_by(merchant_id=mer).count() == initial_count

def test_hitl_3_low_confidence_failed_retry(db):
    mer = "mer_gupta01"
    audio_content = b"fakeaudio" * 200
    initial_count = db.query(LedgerTransaction).filter_by(merchant_id=mer).count()
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract:
             
        mock_stt.return_value = {"transcript": "noise", "language_code": "hi-IN"}
        mock_extract.return_value = {"customer_name": "Suresh", "amount": 500.0, "confidence": 0.20} # < 0.40
        
        response = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        )
        assert response.status_code == 200
        assert response.json()["data"]["outcome"] == "FAILED_RETRY"
        assert db.query(LedgerTransaction).filter_by(merchant_id=mer).count() == initial_count

def test_hitl_4_extraction_raises_failed_retry(db):
    mer = "mer_gupta01"
    audio_content = b"fakeaudio" * 200
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract:
             
        mock_stt.return_value = {"transcript": "500 added", "language_code": "hi-IN"}
        # Simulate extraction throwing an error internally
        mock_extract.side_effect = Exception("Extraction failed completely")
        
        response = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        )
        assert response.status_code == 200
        assert response.json()["data"]["outcome"] == "FAILED_RETRY"

def _get_token_for(merchant_id: str, amount: float = 500.0) -> str:
    from services.voice_service import create_confirmation_token
    return create_confirmation_token(merchant_id, {
        "customer_name": "Suresh",
        "amount": amount,
        "items": [],
        "confidence": 0.60,
        "raw_transcript": "500 added maybe"
    })

def test_hitl_5_valid_token_confirmed_true(db):
    mer = "mer_gupta01"
    token = _get_token_for(mer)
    initial_count = db.query(LedgerTransaction).filter_by(merchant_id=mer).count()
    
    with patch("services.voice_service.sarvam.synthesize_speech") as mock_tts:
        mock_tts.return_value = b"faketts"
        
        response = client.post(
            "/api/v1/voice/confirm-credit",
            json={"merchant_id": mer, "confirmation_token": token, "confirmed": True}
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["outcome"] == "CONFIRMED"
        assert db.query(LedgerTransaction).filter_by(merchant_id=mer).count() == initial_count + 1

def test_hitl_6_valid_token_confirmed_false(db):
    mer = "mer_gupta01"
    token = _get_token_for(mer)
    initial_count = db.query(LedgerTransaction).filter_by(merchant_id=mer).count()
    
    response = client.post(
        "/api/v1/voice/confirm-credit",
        json={"merchant_id": mer, "confirmation_token": token, "confirmed": False}
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["outcome"] == "DISCARDED"
    assert db.query(LedgerTransaction).filter_by(merchant_id=mer).count() == initial_count

def test_hitl_7_tampered_token_rejected(db):
    mer = "mer_gupta01"
    token = _get_token_for(mer)
    
    # Tamper with the token (e.g. changing the last character)
    tampered_token = token[:-1] + ('A' if token[-1] != 'A' else 'B')
    
    response = client.post(
        "/api/v1/voice/confirm-credit",
        json={"merchant_id": mer, "confirmation_token": tampered_token, "confirmed": True}
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["outcome"] == "FAILED_RETRY"

def test_hitl_8_expired_token_rejected(db):
    mer = "mer_gupta01"
    
    # Manually create an expired token
    import jwt, datetime
    token_data = {
        "merchant_id": mer,
        "payload": {"customer_name": "Suresh", "amount": 500, "confidence": 0.60},
        "exp": datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    }
    expired_token = jwt.encode(token_data, settings.INTERNAL_TOKEN, algorithm="HS256")
    
    response = client.post(
        "/api/v1/voice/confirm-credit",
        json={"merchant_id": mer, "confirmation_token": expired_token, "confirmed": True}
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["outcome"] == "FAILED_RETRY"

def test_hitl_9_stress_test_two_confirms(db):
    mer = "mer_gupta01"
    real_initial_count = _check_real_count(mer)
    
    audio_content = b"fakeaudio" * 200
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract, \
         patch("services.voice_service.sarvam.synthesize_speech") as mock_tts:
             
        mock_stt.return_value = {"transcript": "500 added maybe", "language_code": "hi-IN"}
        mock_extract.return_value = {"customer_name": "Suresh", "amount": 500.0, "confidence": 0.60}
        mock_tts.return_value = b"faketts"
        
        # 1. First NEEDS_CONFIRMATION
        res1 = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        ).json()
        token1 = res1["data"]["confirmation_token"]
        
        # 2. Second NEEDS_CONFIRMATION
        res2 = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        ).json()
        token2 = res2["data"]["confirmation_token"]
        
        # 3. Confirm 1 (triggers a DB commit)
        conf1 = client.post(
            "/api/v1/voice/confirm-credit",
            json={"merchant_id": mer, "confirmation_token": token1, "confirmed": True}
        ).json()
        assert conf1["data"]["outcome"] == "CONFIRMED"
        
        # 4. Confirm 2 (triggers a DB commit)
        conf2 = client.post(
            "/api/v1/voice/confirm-credit",
            json={"merchant_id": mer, "confirmation_token": token2, "confirmed": True}
        ).json()
        assert conf2["data"]["outcome"] == "CONFIRMED"
        
        # The fixture sees +2
        assert db.query(LedgerTransaction).filter_by(merchant_id=mer).count() == real_initial_count + 2
        
    # The real DB sees +0 due to isolation
    assert _check_real_count(mer) == real_initial_count
