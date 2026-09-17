# Paytm VyaparSetu — Phase 4 Steps 2–4 Execution Summary

This document summarizes the implementation and verification for **Phase 4 Steps 2–4 (Sarvam AI Integration, Conversational Kirana Extraction, Unit Tests, and Audio Transcribe Route)**.

---

## 1. Implemented Components

### 1. Sarvam Package (`backend/sarvam/`)
- **`client.py`**: Shared HTTP client initialized with base URL `https://api.sarvam.ai` and header `api-subscription-key: <SARVAM_API_KEY>`.
- **`stt.py`**:
  - `transcribe_audio(audio_bytes, filename)`: Submits audio to `https://api.sarvam.ai/speech-to-text` with `model="saaras:v3"`, `mode="codemix"`, and `language_code="hi-IN"`.
- **`tts.py`**:
  - `number_to_hindi_words(n)`: Pure function converting numeric credit amounts into transliterated Hindi words (e.g. `50` $\rightarrow$ `"pachas"`, `60` $\rightarrow$ `"saath"`, `240` $\rightarrow$ `"do sau chalis"`, `300` $\rightarrow$ `"teen sau"`, `1500` $\rightarrow$ `"ek hazaar paanch sau"`).
  - `synthesize_speech(text, target_language_code, speaker)`: Synthesizes text into base64 decoded raw WAV audio using Sarvam API (`bulbul:v3`, speaker `ritu`).
- **`__init__.py`**: Façade exposing strictly `transcribe_audio`, `synthesize_speech`, and `number_to_hindi_words`.

### 2. Conversational Kirana Extraction Package (`backend/extraction/`)
- **`prompts.py`**: Schema definition & system prompt with few-shot kirana udhaar examples.
- **`client.py`**:
  - `extract_entities(transcript)`: Extracts lowercased `customer_name`, numeric `amount`, `items` list, and calculates `confidence` score (e.g. `0.92` for complete name + amount match, `<= 0.5` for missing customer name, and `<= 0.4` for noise/empty text).
- **`__init__.py`**: Façade exposing strictly `extract_entities`.

### 3. API Route (`backend/api/routes/voice.py`)
- **`POST /api/v1/voice/transcribe`**:
  - Accepts multipart audio upload (`UploadFile`).
  - Validates non-empty file payload.
  - Delegates to `sarvam.transcribe_audio()`.
  - Returns standard response envelope: `{"success": true, "data": {"transcript": "...", "language_detected": "hi-IN"}, "error": null}`.

---

## 2. Test Verification

### Run Unit Tests
```powershell
cd paytm-vyaparsetu/backend
python -m pytest -v
```

### Test Results
- **`sarvam/tests/test_sarvam.py`**: **PASSED** (6 offline tests verifying numeric conversions 50, 60, 240, 300, 1500 and façade exports).
- **`extraction/tests/test_extraction.py`**: **PASSED** (6 offline tests verifying Cases 1–5: `suresh` credit, `ramesh` credit, empty string, noise/garbled text, missing customer name, and façade export).
- **`tests/test_voice_transcribe.py`**: **PASSED** (2 route tests verifying `POST /api/v1/voice/transcribe` non-empty file validation and Sarvam delegation).
