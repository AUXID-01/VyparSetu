import os
import sys
import base64
import httpx
from dotenv import load_dotenv

# Reconfigure stdout to support UTF-8 characters on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables from .env file
load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "YOUR_SARVAM_API_KEY_HERE")
HEADERS = {
    "api-subscription-key": SARVAM_API_KEY
}

def test_tts():
    print("[1/2] Testing Sarvam TTS (Text-to-Speech)...")
    url = "https://api.sarvam.ai/text-to-speech"
    payload = {
        "inputs": ["सुरेश जी के खाते में दो सौ चालीस रुपये जोड़ दिए गए हैं।"],
        "target_language_code": "hi-IN",
        "speaker": "ritu",
        "model": "bulbul:v3"
    }
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        # Sarvam returns base64-encoded audio strings in 'audios' list
        audio_b64 = data["audios"][0]
        audio_bytes = base64.b64decode(audio_b64)
        
        output_file = "test_confirmation.wav"
        with open(output_file, "wb") as f:
            f.write(audio_bytes)
            
        print(f"-> Success! Audio saved to {output_file}")
        return output_file

def test_stt(audio_path: str):
    print("[2/2] Testing Sarvam STT (Speech-to-Text) with codemix...")
    url = "https://api.sarvam.ai/speech-to-text"
    
    with open(audio_path, "rb") as f:
        files = {"file": (audio_path, f, "audio/wav")}
        data = {
            "model": "saaras:v3",
            "mode": "codemix",
            "language_code": "hi-IN"
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=HEADERS, data=data, files=files)
            resp.raise_for_status()
            result = resp.json()
            print("-> Success! Raw STT Response:")
            print(result)
            print(f"-> Transcript: {result.get('transcript')}")

if __name__ == "__main__":
    if SARVAM_API_KEY == "YOUR_SARVAM_API_KEY_HERE":
        raise ValueError("Please set SARVAM_API_KEY before running.")
    
    try:
        audio_file = test_tts()
        test_stt(audio_file)
        print("\nAll Sarvam API checks passed! Your credentials and network access are verified.")
    except Exception as e:
        print(f"\nSarvam verification failed: {e}")
        if hasattr(e, "response"):
            print(f"Response details: {e.response.text}")