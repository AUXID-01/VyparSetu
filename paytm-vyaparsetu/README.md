# Paytm VyaparSetu 🚀

VyaparSetu is an AI-powered financial operating system designed for Indian SMBs (kirana stores, wholesalers). It bridges the gap between traditional manual bookkeeping and modern digital ledgers by using cutting-edge AI for Voice, Vision, and Conversational intelligence.

## 🌟 Key Features

### 🎙️ AI Voice Pipeline (Khata by Voice)
Merchants can record a voice note (e.g., *"Suresh ko 50 rupaye ka udhaar diya"*) to instantly log ledger entries.
- **Multi-lingual Support**: Native integration with Sarvam AI supports Hindi, Marathi, Bengali, and more based on the merchant's `preferred_language`.
- **Financial Safety (Atomic Writes)**: Voice transactions are wrapped in strict SQL `savepoints` ensuring that ledger balances and outbox events either succeed entirely or roll back safely.
- **Human-in-the-Loop (HITL)**: If the AI is uncertain about the extracted entities (low confidence due to background noise), the system intercepts the database write and returns a cryptographically signed JWT token to the frontend. The transaction only proceeds when the user taps "Confirm".
- **Smart Formatting**: Converts messy spoken numbers into clean INR formatting automatically.

### 📄 AI Vision Pipeline (Challan OCR)
Automates the tedious task of manual invoice entry.
- **Handwritten & Printed Support**: Upload an image of a challan or invoice. The Vision Stack extracts distributor names, individual items, quantities, and unit prices.
- **Rate-Spike Detection**: Automatically cross-references extracted item prices against historical SQL records for that specific distributor to flag sudden price hikes.
- **Payout Integration**: Drafts automated vendor payouts upon successful challan verification.

### 🧠 Conversational QA (End-to-End Voice BI)
Merchants can "chat" with their business data. The LLM toolsets can dynamically answer natural language queries about distributor supply chains, individual customer balances, and historical challan metadata.
- **Fully Voice Powered**: Merchants can simply tap the microphone in the Business Insights tab, speak a question, and the system will instantly respond by speaking the answer out loud using Sarvam TTS.

### ⚙️ Native Background Workers
Replaced external dependencies (like n8n) with a robust, native asynchronous worker architecture running entirely within Python.
- **Outbox Worker**: Guarantees delivery of webhook payloads.
- **Payout Worker**: Dispatches vendor payments asynchronously.
- **Notification Worker**: Sends SMS/WhatsApp alerts for outbox events.

---

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Alembic (Migrations)
- **Database**: PostgreSQL (Cloud hosted via Supabase)
- **AI / LLMs**: Groq (Llama 3), Google Cloud Vision, Sarvam AI (Indic STT/TTS)
- **Frontend**: React (Vite / Bolt.new)

---

## 🚀 Quick Start Guide

### 1. Environment Setup
Create a `.env` file in the `backend/` directory using `.env.example` as a template.
Ensure you add your API keys and your Supabase connection string:
```ini
DATABASE_URL=postgresql://postgres.[project-id]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
GROQ_API_KEY=your_key
SARVAM_API_KEY=your_key
GOOGLE_VISION_API_KEY=your_key
VOICE_CONFIRMATION_SECRET=any_random_secure_string
```

### 2. Database Migrations
VyaparSetu uses Alembic to manage database schema. Since you are connecting to a cloud database (like Supabase), simply apply the migrations:
```bash
cd backend
alembic upgrade head
```

### 3. Seed Demo Data
Populate your cloud database with demo merchants, distributors, and historical ledger data to test the UI:
```bash
python -m scripts.seed_demo
```

### 4. Run the Application
Start the FastAPI backend:
```bash
uvicorn main:app --reload
```

Start the React frontend (in a separate terminal):
```bash
cd project
npm install
npm run dev
```

---

## 📂 Architecture Note
* **`backend/api/`**: FastAPI routes and endpoints.
* **`backend/db/`**: SQLAlchemy models, Repositories, and Alembic migrations.
* **`backend/services/`**: Core business logic and orchestration.
* **`backend/workers/`**: Asynchronous background tasks (Outbox, Payouts).
* **`backend/sarvam/ & vision/`**: Wrappers for external AI provider APIs.
* **`project/src/pages/Insights.tsx`**: Location of the new end-to-end Voice QA dictation and playback feature.
