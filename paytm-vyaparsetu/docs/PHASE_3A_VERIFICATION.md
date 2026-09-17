# Paytm VyaparSetu — Core Foundation & Database Verification Guide (Phase 3A)

This document details the verification commands for **Phase 3A (Core Architecture & Database Layer)**. It explains **what each command does**, **why we are using it**, and **what specific output to look for**.

---

## 1. Directory Context & Working Directory Rule

> **IMPORTANT**: The Python packages `core`, `db`, and `config` live inside the [`backend/`](file:///c:/VyaparSetu/VyparSetu/paytm-vyaparsetu/backend) directory. When executing module verification commands, always ensure you are inside `paytm-vyaparsetu/backend` so Python can resolve local imports (`from core import ...`, `from db import ...`).

```powershell
cd paytm-vyaparsetu/backend
```

---

## 2. Verification Commands Breakdown

### Command 1: Database Schema & Index Verification

#### Command:
```powershell
python -c "import psycopg2; conn=psycopg2.connect('postgresql://vyapar_user:vyapar_pass@localhost:5432/vyaparsetu_db'); cur=conn.cursor(); cur.execute('SELECT table_name FROM information_schema.tables WHERE table_schema=\'public\' AND table_type=\'BASE TABLE\';'); print('PostgreSQL Tables:', sorted([r[0] for r in cur.fetchall()])); cur.execute('SELECT indexname FROM pg_indexes WHERE schemaname=\'public\';'); print('Indexes:', [r[0] for r in cur.fetchall() if 'idx_' in r[0]]); cur.close(); conn.close()"
```

#### What it does:
Queries PostgreSQL's system catalog (`information_schema` and `pg_indexes`) via direct `psycopg2` driver to check table creation and index definitions.

#### Why we are using it:
To verify that Alembic migration applied the **10 Master Schema tables** and custom performance indexes (`idx_outbox_pending`, `idx_ledger_customer`, `idx_ledger_date`, `idx_line_item_rate_lookup`) to PostgreSQL without schema drift or missing constraints.

#### What output to look for:
- `PostgreSQL Tables`: Must contain all 10 tables: `['alembic_version', 'alerts', 'customers', 'distributors', 'insight_cache', 'invoice_line_items', 'invoices', 'ledger_transactions', 'merchants', 'outbox_events', 'settlement_daily_rollups']`
- `Indexes`: Must list `['idx_outbox_pending', 'idx_ledger_customer', 'idx_ledger_date', 'idx_line_item_rate_lookup']`

---

### Command 2: Core Helpers & Database ORM Persistence Verification

#### Command:
```powershell
python -c "import random; from core import generate_merchant_id, generate_customer_id, generate_settlement_id, TxnType, ErrorCode, success_envelope, error_envelope; from db import SessionLocal; from db.models import Merchant, Customer; m_id = generate_merchant_id(); c_id = generate_customer_id(); rand_phone = f'+919{random.randint(100000000, 999999999)}'; db = SessionLocal(); mer = Merchant(merchant_id=m_id, shop_name='Test Shop', owner_name='Ramesh', phone=rand_phone, cognee_dataset=f'merchant_{m_id}'); db.add(mer); db.flush(); cus = Customer(customer_id=c_id, merchant_id=m_id, display_name='Suresh', canonical_key='suresh', phone='+919876543210'); db.add(cus); db.commit(); fetched = db.query(Merchant).filter_by(merchant_id=m_id).first(); print('Persistence Verified! Shop Owner:', fetched.owner_name); db.delete(cus); db.delete(mer); db.commit(); db.close()"
```

#### What it does:
1. Tests prefixed ID generators (`generate_merchant_id()`, `generate_customer_id()`, `generate_settlement_id()`).
2. Tests `StrEnum` definitions (`TxnType`, `ErrorCode`) and JSON response envelopes (`success_envelope`, `error_envelope`).
3. Opens a SQLAlchemy session via `SessionLocal()`, writes a `Merchant` and `Customer` record into PostgreSQL, reads them back, and cleans up test data.

#### Why we are using it:
To ensure the application layer (`core`) and the database persistence layer (`db.models` & `db.session`) communicate seamlessly with PostgreSQL, foreign key relationships hold, and session lifecycle management works before writing REST route endpoints.

#### What output to look for:
```text
Persistence Verified! Shop Owner: Ramesh
```

---

### Command 3: Alembic Migration Status Check

#### Command:
```powershell
python -m alembic current
```

#### What it does:
Inspects the current migration revision recorded in PostgreSQL (`alembic_version` table) against Alembic revision files in `db/migrations/versions/`.

#### Why we are using it:
To ensure the local database schema is fully up-to-date with the latest revision header (`head`).

#### What output to look for:
```text
f5c288e9ff4d (head)
```

---

### Command 4: Standalone Sarvam Voice API Verification

#### Command:
```powershell
python tests/test_sarvam_standalone.py
```

#### What it does:
1. Calls Sarvam AI Text-to-Speech (`bulbul:v3`, speaker `ritu`) with Hindi sample text and saves output to `test_confirmation.wav`.
2. Sends the synthesized WAV audio back to Sarvam AI Speech-to-Text (`saaras:v3`, mode `codemix`) and prints the returned transcript.

#### Why we are using it:
To isolate external API credentials (`SARVAM_API_KEY`) and network access from app routing, ensuring speech services are operational before wiring voice pipelines in Phase 4.

#### What output to look for:
```text
[1/2] Testing Sarvam TTS (Text-to-Speech)...
-> Success! Audio saved to test_confirmation.wav
[2/2] Testing Sarvam STT (Speech-to-Text) with codemix...
-> Success! Raw STT Response:
{'request_id': '...', 'transcript': 'सुरेश जी के खाते में ₹240 जोड़ दिए गए हैं।', 'language_code': 'hi-IN'}
-> Transcript: सुरेश जी के खाते में ₹240 जोड़ दिए गए हैं।

All Sarvam API checks passed! Your credentials and network access are verified.
```

---

## 3. Quick Summary Table

| Goal | Command (run from `backend/`) | Success Marker |
|---|---|---|
| Verify 10 Tables & Indexes | `python -c "import psycopg2; ..."` | `All 10 tables present` |
| Test Core & ORM Persistence | `python -c "import random; from core ..."` | `Persistence Verified! Shop Owner: Ramesh` |
| Check Alembic Head | `python -m alembic current` | `(head)` |
| Test Sarvam STT & TTS | `python tests/test_sarvam_standalone.py` | `All Sarvam API checks passed!` |
