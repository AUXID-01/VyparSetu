# Phase 3C Completion Summary

## What Was Accomplished

### 1. API Dependencies & Auth (`api/deps.py`, `core/auth.py`)
- Created `get_current_merchant` dependency that intercepts the `Authorization: Bearer <token>` header and decodes mock session tokens (`mock_tok_mer_...`).
- Created `verify_internal_token` dependency that strictly checks the `X-Internal-Token` header against the system configuration.

### 2. Merchants Routes (`api/routes/merchants.py`)
- Implemented `POST /api/v1/merchants` to create new merchant accounts.
- Added strict uniqueness constraint handling for phone numbers, raising the canonical `DUPLICATE_MERCHANT_PHONE` error if a conflict exists.
- Corrected the `cognee_dataset` generation to strictly follow the `merchant_{merchant_id}` format as per the Master Schema.

### 3. Voice Service & Routes (`services/voice_service.py`, `api/routes/voice.py`)
- Implemented `POST /api/v1/voice/log-credit` using mocked extracted JSON input.
- Sequenced the exact required database flow:
  1. Resolve or create customer (using the `canonical_key` logic).
  2. Insert `LedgerTransaction` (type: `CREDIT_ADDED`, source: `VOICE`).
  3. Insert `OutboxEvent` (type: `CREDIT_ADDED`, default `PENDING`).
- Implemented the SQLAlchemy query logic to dynamically calculate the latest `total_due` after inserting the new credit transaction.
- Formulated the Hindi verification response text (`"Suresh ji ke khate mein 240 rupaye jod diye gaye hain."`).

### 4. Query Routes (`api/routes/query.py`)
- Implemented `GET /api/v1/query/customer-due/{customer_id}` returning a live SQLAlchemy summation of `CREDIT_ADDED` minus `CREDIT_PAID`.
- Implemented `GET /api/v1/query/daily-summary` computing live daily transaction totals.

---

## Commands to Run Locally

If you are cloning this repository on a fresh machine or need to reset your state, run the following commands in the `paytm-vyaparsetu` directory:

### 1. Start the FastAPI Server
Spin up the Uvicorn development server:
```bash
cd backend
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
# source venv/bin/activate

uvicorn main:app --port 8000 --reload
```

### 2. Run the Phase 3C Verification Script
Open a **new, separate terminal tab**, activate your python environment, and run the automated test:
```bash
cd backend
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
# source venv/bin/activate

python verify_3c.py
```

*Expected Flow & Output:*
The script handles 4 sequential API requests:
1. Creates a merchant (generates a random phone suffix to bypass duplication errors across multiple runs).
2. Logs a ₹240 credit for "Suresh".
3. Logs a ₹60 credit for "suresh" (testing the canonical deduplication over HTTP).
4. Queries the ledger balance, returning exactly `300.0`.
