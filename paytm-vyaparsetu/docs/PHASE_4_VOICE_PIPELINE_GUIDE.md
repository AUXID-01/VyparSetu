# Paytm VyaparSetu — Voice Credit Pipeline Guide & Testing (Phase 4)

This document provides a complete guide for the **Counter-Speed Voice Credit Pipeline (Phase 4)**, including architecture details, API contracts, automated testing, manual Postman/cURL testing, and database verification.

---

## 1. Pipeline Architecture & Flow

```
[Audio Clip (.wav / .mp3 / .webm)]
       │
       ▼
[POST /api/v1/voice/log-credit-from-audio]
       │
       ├─► 1. Input Guard (audio_bytes >= 1000 bytes)
       │
       ├─► 2. Sarvam Speech-to-Text (saaras:v3, codemix hi-IN)
       │      └─► Output: Raw Hindi / Hinglish Transcript (Devanagari / Latin)
       │
       ├─► 3. Kirana Entity Extraction Engine
       │      └─► Parses: customer_name, numeric amount (from digits or Devanagari words), items, confidence
       │
       ├─► 4. Low Confidence Guard (confidence >= 0.6 & valid name & amount > 0)
       │      └─► If failed: returns 400 Bad Request (LOW_CONFIDENCE_EXTRACTION)
       │
       ├─► 5. PostgreSQL Invariants (Atomic DB Write)
       │      ├─► Resolve/Create Customer (canonical_key dedup)
       │      ├─► Insert LedgerTransaction (CREDIT_ADDED, VOICE)
       │      ├─► Insert OutboxEvent (CREDIT_ADDED, PENDING status)
       │      └─► Calculate Updated Total Customer Due
       │
       └─► 6. Spoken Feedback Audio Generation
              ├─► Number-to-Hindi-Words (e.g. 3340 -> "teen hazaar teen sau chalis")
              ├─► Formats soundbox message: "{customer_name} ji ke khate mein {words} rupaye jod diye gaye hain."
              ├─► Sarvam Text-to-Speech (bulbul:v3, speaker: ritu)
              └─► Returns JSON envelope with confirmation_audio_text & base64 WAV audio
```

---

## 2. API Endpoints

### 2.1 Audio Transcription Only
- **Method & Path**: `POST /api/v1/voice/transcribe`
- **Request Body**: `multipart/form-data`
  - `audio`: Audio File (`UploadFile`)
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "transcript": "नंदिनी के खाता में ₹340 डाल दो",
      "language_detected": "hi-IN"
    },
    "error": null
  }
  ```

### 2.2 Full Voice Credit Fast-Path
- **Method & Path**: `POST /api/v1/voice/log-credit-from-audio`
- **Request Body**: `multipart/form-data`
  - `merchant_id`: String (e.g. `mer_test_01`)
  - `audio`: Audio File (`UploadFile`)
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "txn_id": "txn_255b3b",
      "customer_id": "cus_1d25ae",
      "new_balance": 3340.0,
      "confirmation_audio_text": "नरेन्द्र ji ke khate mein teen hazaar teen sau chalis rupaye jod diye gaye hain.",
      "confirmation_audio_b64": "UklGRvAZAwBXQVZF..."
    },
    "error": null
  }
  ```

---

## 3. How to Test

### Method A: Automated Pytest Suite (Zero Network Calls)

Run all offline unit tests covering number-to-words, entity extractions, and route validation:

```powershell
# Navigate to backend folder
cd paytm-vyaparsetu/backend

# Activate virtual environment
..\venv\Scripts\Activate.ps1

# Run pytest
python -m pytest -v
```

*Expected Result: `15 passed in ~2.90s`*

---

### Method B: End-to-End Verification Script

Run the automated E2E script that tests the input guard, fast-path audio pipeline, and PostgreSQL database invariants:

```powershell
cd paytm-vyaparsetu/backend
python scripts/test_voice_e2e.py
```

*Expected Output:*
```text
[1/4] Using existing merchant: mer_test_01
[2/4] Testing empty audio clip error response...
  -> Passed! Empty audio clip correctly returned 400 LOW_CONFIDENCE_EXTRACTION
[3/4] Testing full voice credit pipeline...
  -> Passed! Txn ID: txn_7d7f29, Balance: ₹480.0
[4/4] Verifying database invariants in PostgreSQL...
  -> Passed! Postgres ledger row & PENDING outbox event verified!

ALL Voice E2E Pipeline Checks Passed Successfully!
```

---

### Method C: Manual Testing via cURL or Postman

#### 1. Start the FastAPI Server:
```powershell
cd paytm-vyaparsetu/backend
uvicorn main:app --reload --port 8000
```

#### 2. Send Audio File via cURL:
```powershell
curl -X POST "http://localhost:8000/api/v1/voice/log-credit-from-audio" `
  -F "merchant_id=mer_test_01" `
  -F "audio=@C:\path\to\your\audio_sample.wav"
```

---

### Method D: Database Verification (`psql` CLI)

Open `psql` inside your running Docker container to inspect real-time database records:

```powershell
docker exec -it vyaparsetu_postgres psql -U vyapar_user -d vyaparsetu_db
```

#### Query 1: Verify Ledger Transaction
```sql
SELECT txn_id, merchant_id, customer_id, amount, txn_type, source, extraction_confidence, created_at 
FROM ledger_transactions 
ORDER BY created_at DESC 
LIMIT 3;
```

#### Query 2: Verify Pending Outbox Events (for n8n polling)
```sql
SELECT event_id, merchant_id, event_type, status, payload 
FROM outbox_events 
ORDER BY created_at DESC 
LIMIT 3;
```

#### Query 3: Verify Customer Canonical Key Deduplication
```sql
SELECT customer_id, merchant_id, display_name, canonical_key, created_at 
FROM customers 
ORDER BY created_at DESC;
```
