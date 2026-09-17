from .client import get_sarvam_client, get_sarvam_headers, SARVAM_BASE_URL
import httpx

def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    """
    Transcribes audio bytes into text using Sarvam AI Speech-to-Text API (saaras:v3 codemix).
    """
    url = f"{SARVAM_BASE_URL}/speech-to-text"
    headers = get_sarvam_headers()
    
    files = {"file": (filename, audio_bytes, "audio/wav")}
    data = {
        "model": "saaras:v3",
        "mode": "codemix",
        "language_code": "hi-IN",
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, data=data, files=files)
        response.raise_for_status()
        res_json = response.json()
        
    return {
        "transcript": res_json.get("transcript", ""),
        "language_code": res_json.get("language_code", "hi-IN"),
    }
