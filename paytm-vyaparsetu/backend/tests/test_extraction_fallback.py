import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__)))

from extraction.client import extract_entities
from core.errors import ExtractionFailedError
from services.voice_service import process_voice_credit_audio

def test_extraction_failure_raises_error_and_no_writes():
    db = MagicMock()
    merchant_id = "test_merchant"
    
    with patch("extraction.client.get_groq_client") as mock_groq_client, \
         patch("services.voice_service.sarvam.transcribe_audio") as mock_stt:
             
        # Mock STT to return the transcript that would have triggered regex fallback
        mock_stt.return_value = {
            "transcript": "bhaiya 50 rupaye tel likho",
            "language_code": "hi-IN"
        }
        
        # Mock Groq to raise an exception to simulate failure
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.side_effect = Exception("Groq API Timeout")
        mock_groq_client.return_value = mock_client_instance
        
        # Simulate processing the audio
        audio_bytes = b"fake_audio_content_that_is_at_least_1000_bytes_long" * 100
        
        # Act & Assert A: ExtractionFailedError is raised
        with pytest.raises(ExtractionFailedError) as exc_info:
            process_voice_credit_audio(db, merchant_id, audio_bytes, request_id="req_test_123")
            
        assert exc_info.value.code == "EXTRACTION_FAILED"
        
        # Assert B & C: No rows written to ledger_transactions or customers
        # (Since db is a mock, we verify no db.add or db.commit was called for this operation)
        db.add.assert_not_called()
        db.commit.assert_not_called()
