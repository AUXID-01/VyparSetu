import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sarvam.tts import synthesize_speech
from sarvam.stt import transcribe_audio

def run_diagnostic():
    tests = [
        ("D", "कुल राशि 150000 रुपये"),
        ("E", "कुल राशि 150000.0 रुपये"),
        ("F", "कुल राशि 150000.5 रुपये")
    ]
    
    for label, text in tests:
        audio_bytes = synthesize_speech(text, target_language_code="hi-IN", speaker="ritu", request_id=f"diag_{label}")
        stt_res = transcribe_audio(audio_bytes, filename=f"diag_{label}.wav", request_id=f"diag_{label}")
        print(f"{label}: '{text}' -> STT: '{stt_res.get('transcript', '')}'")
            
if __name__ == "__main__":
    run_diagnostic()
