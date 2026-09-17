from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

client = TestClient(app)

def test_transcribe_empty_file():
    response = client.post("/api/v1/voice/transcribe", files={"audio": ("empty.wav", b"", "audio/wav")})
    assert response.status_code == 400
    res_json = response.json()
    assert res_json["success"] is False
    assert res_json["error"]["code"] == "LOW_CONFIDENCE_EXTRACTION"

@patch("sarvam.transcribe_audio")
def test_transcribe_success(mock_transcribe):
    mock_transcribe.return_value = {
        "transcript": "suresh ji 240 rupaye ka dahi",
        "language_code": "hi-IN"
    }
    
    response = client.post(
        "/api/v1/voice/transcribe",
        files={"audio": ("test.wav", b"dummy audio content", "audio/wav")}
    )
    
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["transcript"] == "suresh ji 240 rupaye ka dahi"
    assert res_json["data"]["language_detected"] == "hi-IN"
