# Paytm VyaparSetu — Environment Setup & Verification Guide

This guide provides step-by-step instructions for bootstrapping, setting up, running, and verifying the **Paytm VyaparSetu** environment locally.

---

## 1. Prerequisites

Ensure you have the following installed on your system before proceeding:

- **Python**: 3.11.0 or higher ([Download Python](https://www.python.org/downloads/))
- **Docker**: Docker Desktop with Docker Compose v2 ([Download Docker](https://www.docker.com/products/docker-desktop/))
- **Git**: Latest version ([Download Git](https://git-scm.com/))
- **Sarvam AI API Key**: Get your API key from [Sarvam AI Dashboard](https://dashboard.sarvam.ai)

---

## 2. Environment Configuration (`.env`)

1. Navigate to the root directory of the project:
   ```powershell
   cd paytm-vyaparsetu
   ```

2. Copy `.env.example` to create your local `.env` file:
   ```powershell
   cp .env.example .env
   ```

3. Open `.env` and set your actual Sarvam API key:
   ```env
   # PostgreSQL Container Settings
   POSTGRES_USER=vyapar_user
   POSTGRES_PASSWORD=vyapar_pass
   POSTGRES_DB=vyaparsetu_db
   POSTGRES_PORT=5432

   # Database Connection String
   DATABASE_URL=postgresql://vyapar_user:vyapar_pass@localhost:5432/vyaparsetu_db

   # External API Keys
   SARVAM_API_KEY=sk_your_actual_sarvam_api_key_here

   # Security & Authentication
   INTERNAL_TOKEN=vyapar_internal_secret_token_123

   # Server Settings
   PORT=8000
   ENVIRONMENT=development

   # n8n Webhook Triggers
   N8N_PAYMENT_LINK_WEBHOOK_URL=http://localhost:5678/webhook/payment-link
   N8N_VENDOR_PAYOUT_WEBHOOK_URL=http://localhost:5678/webhook/vendor-payout
   N8N_ALERT_DISPATCH_WEBHOOK_URL=http://localhost:5678/webhook/alert-dispatch
   N8N_ONBOARDING_WEBHOOK_URL=http://localhost:5678/webhook/merchant-onboarding
   ```

---

## 3. Virtual Environment Setup & Dependencies Installation

Always use an isolated Python virtual environment:

### Step 3.1: Create Virtual Environment
```powershell
python -m venv venv
```

### Step 3.2: Activate Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **Linux / macOS / Git Bash**:
  ```bash
  source venv/bin/activate
  ```

*(You should now see `(venv)` prefixed in your terminal command line)*

### Step 3.3: Install Pinned Dependencies
```powershell
pip install -r backend/requirements.txt
```

---

## 4. Local PostgreSQL Stack (Docker Compose)

Start the local PostgreSQL 16 database container in detached mode:

```powershell
docker compose up -d db
```

### Check Container Status
Verify that the `vyaparsetu_postgres` container is running and healthy:
```powershell
docker compose ps
```
*Expected output: Status should show `Up (healthy)` and port `0.0.0.0:5432->5432/tcp`.*

---

## 4.1. Database Migrations (Applying Schema Updates)

Whenever you set up the project for the first time or pull new schema changes from `main`, run Alembic to apply all migrations to your local PostgreSQL instance:

```powershell
# 1. Navigate to backend directory
cd paytm-vyaparsetu/backend

# 2. Apply all database migrations
alembic upgrade head
```

> ⚠️ **Important Note**: Starting the Docker container alone runs PostgreSQL with your local state. Running `alembic upgrade head` is what updates your local database tables to the latest schema (creating/extending `invoices`, `invoice_line_items`, `invoice_packaging_adjustments`, `invoice_extraction_audit`, etc.).


---

## 5. Verification Steps

### Verification Step 1: Test Database Connectivity
Run the following python snippet from your active virtual environment to confirm connection to PostgreSQL on port 5432:

```powershell
python -c "import psycopg2; conn=psycopg2.connect('postgresql://vyapar_user:vyapar_pass@localhost:5432/vyaparsetu_db'); cur=conn.cursor(); cur.execute('SELECT version();'); print('✅ DB Connected! Version:', cur.fetchone()[0]); cur.close(); conn.close()"
```

*Expected output:*
```text
✅ DB Connected! Version: PostgreSQL 16.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
```

---

### Verification Step 2: Testing Till Sarvam Standalone

Test Sarvam Text-to-Speech (TTS) voice audio synthesis and Speech-to-Text (STT) codemix transcription end-to-end:

```powershell
python backend/tests/test_sarvam_standalone.py
```

*Expected output:*
```text
[1/2] Testing Sarvam TTS (Text-to-Speech)...
-> Success! Audio saved to test_confirmation.wav
[2/2] Testing Sarvam STT (Speech-to-Text) with codemix...
-> Success! Raw STT Response:
{'request_id': '20260917_xxxx', 'transcript': 'सुरेश जी के खाते में ₹240 जोड़ दिए गए हैं।', 'language_code': 'hi-IN'}
-> Transcript: सुरेश जी के खाते में ₹240 जोड़ दिए गए हैं।

All Sarvam API checks passed! Your credentials and network access are verified.
```

---

### Verification Step 3: Phase 3A Core Foundation & Database ORM Check

For detailed instructions on testing ID generators, string enums, error envelopes, and SQLAlchemy ORM database persistence, see **[docs/PHASE_3A_VERIFICATION.md](file:///c:/VyaparSetu/VyparSetu/paytm-vyaparsetu/docs/PHASE_3A_VERIFICATION.md)**.

---

## 6. Helpful Commands Reference

| Action | Command |
|---|---|
| Activate Venv | `.\venv\Scripts\Activate.ps1` |
| Stop Postgres Container | `docker compose down` |
| Restart Postgres Container | `docker compose restart db` |
| View Postgres Logs | `docker logs vyaparsetu_postgres` |
| Re-run Sarvam Verification | `python backend/tests/test_sarvam_standalone.py` |
