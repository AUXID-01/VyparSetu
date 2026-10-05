import pytest
import sys
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from db.session import SessionLocal, engine
from api.deps import get_db
from db.models import Merchant, LedgerTransaction
from sqlalchemy.orm import sessionmaker

client = TestClient(app)

import sqlalchemy

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

def test_gupta_default_resolution(db):
    mer_gupta = "mer_gupta01"
    audio_content = b"fakeaudio" * 200
    
    initial_count = db.query(LedgerTransaction).filter_by(merchant_id=mer_gupta).count()
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract, \
         patch("services.voice_service.sarvam.synthesize_speech") as mock_tts:
             
        mock_stt.return_value = {"transcript": "500 added", "language_code": "hi-IN"}
        mock_extract.return_value = {"customer_name": "Suresh", "amount": 500.0, "confidence": 0.9}
        mock_tts.return_value = b"faketts"
        
        response = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer_gupta},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        )
        assert response.status_code == 200
        mock_stt.assert_called_once()
        assert mock_stt.call_args[1]["language"] == "hi"
        
        # Verify it was written inside our test transaction
        assert db.query(LedgerTransaction).filter_by(merchant_id=mer_gupta).count() == initial_count + 1
        
        # Prove isolation holds by checking a separate DB session that bypasses our fixture
        from db.session import SessionLocal
        isolated_db = SessionLocal()
        try:
            assert isolated_db.query(LedgerTransaction).filter_by(merchant_id=mer_gupta).count() == initial_count
        finally:
            isolated_db.close()

def test_shinde_default_resolution(db):
    mer_shinde = "mer_shinde01"
    audio_content = b"fakeaudio" * 200
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract, \
         patch("services.voice_service.sarvam.synthesize_speech") as mock_tts:
             
        mock_stt.return_value = {"transcript": "500 added", "language_code": "mr-IN"}
        mock_extract.return_value = {"customer_name": "Ganesh", "amount": 500.0, "confidence": 0.9}
        mock_tts.return_value = b"faketts"
        
        response = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer_shinde},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        )
        assert response.status_code == 200
        mock_stt.assert_called_once()
        assert mock_stt.call_args[1]["language"] == "mr"

def test_shinde_override_resolution(db):
    mer_shinde = "mer_shinde01"
    audio_content = b"fakeaudio" * 200
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract, \
         patch("services.voice_service.sarvam.synthesize_speech") as mock_tts:
             
        mock_stt.return_value = {"transcript": "500 added", "language_code": "bn-IN"}
        mock_extract.return_value = {"customer_name": "Ganesh", "amount": 500.0, "confidence": 0.9}
        mock_tts.return_value = b"faketts"
        
        response = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer_shinde, "language_override": "bn"},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        )
        assert response.status_code == 200
        mock_stt.assert_called_once()
        # Assert A: override locale code
        assert mock_stt.call_args[1]["language"] == "bn"
        
        # Assert B: stored preferred_language is unchanged
        db.expire_all()
        shinde_db = db.query(Merchant).filter_by(merchant_id=mer_shinde).first()
        assert shinde_db.preferred_language == "mr"

def test_unsupported_language_raises():
    import sarvam.stt
    from core.errors import AppException
    
    audio_content = b"fakeaudio" * 200
    with pytest.raises(AppException) as exc:
        sarvam.stt.transcribe_audio(audio_content, language="invalid-code")
    
    assert exc.value.code == "UNSUPPORTED_LANGUAGE"
    assert exc.value.status_code == 400

def test_locale_mapping_all_supported():
    from sarvam.stt import LANGUAGE_MAPPING
    
    # Explicitly hardcoded expected mapping instead of dynamically generating it
    # This ensures both that all codes are supported AND that they map precisely.
    expected_mapping = {
        "hi": "hi-IN",
        "mr": "mr-IN",
        "bn": "bn-IN",
        "gu": "gu-IN",
        "ta": "ta-IN",
        "te": "te-IN",
        "kn": "kn-IN",
        "ml": "ml-IN",
        "pa": "pa-IN",
        "od": "od-IN",
        "en": "en-IN"
    }
    
    for short_code, expected_suffix in expected_mapping.items():
        assert short_code in LANGUAGE_MAPPING, f"Missing mapping for {short_code}"
        assert LANGUAGE_MAPPING[short_code] == expected_suffix, f"Mapping {short_code} did not map to {expected_suffix}"
        
    # Also verify there are no unexpected keys
    assert len(LANGUAGE_MAPPING) == len(expected_mapping)

def test_savepoint_stress_across_multiple_commits(db):
    from db.session import SessionLocal
    mer_gupta = "mer_gupta01"
    audio_content = b"fakeaudio" * 200
    
    # Check real DB before we start
    isolated_db_before = SessionLocal()
    initial_real_count = isolated_db_before.query(LedgerTransaction).filter_by(merchant_id=mer_gupta).count()
    isolated_db_before.close()
    
    with patch("services.voice_service.sarvam.transcribe_audio") as mock_stt, \
         patch("services.voice_service.extraction.extract_entities") as mock_extract, \
         patch("services.voice_service.sarvam.synthesize_speech") as mock_tts:
             
        mock_stt.return_value = {"transcript": "500 added", "language_code": "hi-IN"}
        mock_extract.return_value = {"customer_name": "Suresh", "amount": 500.0, "confidence": 0.9}
        mock_tts.return_value = b"faketts"
        
        # First call (First internal DB commit)
        response1 = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer_gupta},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        )
        assert response1.status_code == 200
        
        # Second call (Second internal DB commit)
        response2 = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": mer_gupta},
            files={"audio": ("test.wav", audio_content, "audio/wav")}
        )
        assert response2.status_code == 200
        
        # Verify the fixture's transaction sees BOTH rows
        assert db.query(LedgerTransaction).filter_by(merchant_id=mer_gupta).count() == initial_real_count + 2
        
        # Verify the REAL DB sees 0 new rows despite the 2 commits!
        isolated_db_after = SessionLocal()
        try:
            assert isolated_db_after.query(LedgerTransaction).filter_by(merchant_id=mer_gupta).count() == initial_real_count
        finally:
            isolated_db_after.close()
