# Paytm VyaparSetu v2

**The Intelligent Khata & Ledger Management System for Indian Merchants**

## 👋 What is VyaparSetu?

VyaparSetu v2 is an AI-powered platform designed to replace the traditional *Bahi Khata* (credit notebook). It helps Kirana store owners manage credit, digitize vendor bills, and automate payments—all at lightning speed.

### ✨ Key Features

1. 🎙️ **Voice-Powered Khata (< 500ms):** Log customer credit simply by speaking in Hindi/Hinglish. (Powered by Sarvam AI & Groq Llama-3).
2. 📄 **Smart Challan Lens (< 3.5s):** Take a photo of a vendor's paper bill. VyaparSetu instantly extracts all items and detects hidden price hikes. (Powered by Google Vision OCR).
3. 🧠 **Instant Business Q&A:** Ask questions like *"Suresh ka kitna baaki hai?"* and get instant answers directly from your database.
4. ⚡ **Automated WhatsApp Links:** Automatically send UPI payment links and reminders to customers via n8n orchestrations.

---

## 🏗️ Tech Stack

Built for maximum speed and data privacy, running entirely on your local machine:
- **Frontend:** React, Vite, Tailwind CSS
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** Native PostgreSQL (The single source of truth)
- **AI Models:** Sarvam AI (Speech), Groq (Fast Inference), Google Vision (OCR)
- **Automation:** n8n (Local Docker Orchestrator)

---

## 🚀 Getting Started (Beginner Guide)

Follow these steps to run VyaparSetu locally on your computer.

### Prerequisites
- **Python** (3.11+)
- **Node.js**
- **Docker Desktop**

### 1. Configure the Environment
```bash
cd paytm-vyaparsetu
cp backend/.env.example backend/.env
```
*(Add your Sarvam, Groq, and Google Vision API keys in the `.env` file).*

### 2. Start PostgreSQL & n8n (Database & Automation)
```bash
docker compose up -d
```
*(This starts the database and local n8n on `http://localhost:5678`).*

### 3. Start the Backend API
Open a terminal in the `paytm-vyaparsetu/backend` folder:
```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```
*(Runs on `http://localhost:8000`).*

### 4. Start the Frontend
Open a **new** terminal in the `paytm-vyaparsetu/project` folder:
```bash
npm install
npm run dev
```
*(Runs on `http://localhost:5173`).*

🎉 **You're all set!** Open the frontend link in your browser.

---

## 📚 Documentation
For deep dives into the system design, check the `docs/` folder:
- [Architecture Flow](paytm-vyaparsetu/docs/vyaparsetu_architecture_v2.md)
- [PostgreSQL Guide](paytm-vyaparsetu/docs/POSTGRES_OPS_GUIDE.md)
