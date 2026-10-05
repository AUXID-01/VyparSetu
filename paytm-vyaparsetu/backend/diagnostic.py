import os
import sys
import base64

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import settings
from sarvam.tts import synthesize_speech
from sarvam.stt import transcribe_audio

def run_diagnostic():
    tests = [
        ("A", "आपका कुल बकाया है 150.50 रुपये"),
        ("B", "कुल राशि 1,50,000 रुपये"),
        ("C", "शेष राशि 12,34,567.89 रुपये")
    ]
    
    results = []
    for label, text in tests:
        print(f"\\n--- Testing {label}: '{text}' ---")
        try:
            # 1. Synthesize Speech
            audio_bytes = synthesize_speech(text, target_language_code="hi-IN", speaker="ritu", request_id=f"diag_{label}")
            print(f"TTS generated {len(audio_bytes)} bytes.")
            
            # Save to disk so you can listen to it!
            wav_path = os.path.join(os.path.dirname(__file__), f"diag_{label}.wav")
            with open(wav_path, "wb") as f:
                f.write(audio_bytes)
            print(f"Saved audio to: {wav_path}")
            
            # 2. Transcribe the generated audio
            stt_res = transcribe_audio(audio_bytes, filename=f"diag_{label}.wav", request_id=f"diag_{label}")
            transcript = stt_res.get("transcript", "")
            print(f"STT Transcript: '{transcript}'")
            results.append((label, text, transcript))
        except Exception as e:
            print(f"Error on {label}: {e}")
            
if __name__ == "__main__":
    run_diagnostic()
