# Paytm VyaparSetu 🚀

**The Intelligent Khata & Ledger Management System for Indian Merchants**

## 🇮🇳 Our Mission: How We Are Helping
For decades, Indian SMBs and Kirana store owners have relied on the traditional *Bahi Khata* (physical credit notebooks) and manual paper bills. Digitizing these records is often a massive friction point because it requires tedious manual data entry on small screens after a long working day.

**VyaparSetu** completely eliminates this friction. We are helping merchants digitize their entire business simply by **speaking** or **taking photos**. Our platform bridges the gap between traditional bookkeeping and modern digital ledgers by utilizing state-of-the-art AI.

## ✨ Key Capabilities

1. 🎙️ **Khata By Voice (Native Language Support)**
   Merchants can simply speak to log transactions (e.g., *"Suresh ko 50 rupaye ka udhaar diya"*). 
   - Powered by **Sarvam AI** for local language understanding (Hindi, Marathi, Bengali, etc.).
   - Includes **Human-In-The-Loop (HITL)** safeguards so merchants always verify the AI's math before financial writes occur.

2. 📄 **Smart Challan Lens (Computer Vision)**
   Merchants take a photo of a vendor's paper bill, and our Vision Stack instantly digitizes it.
   - Extracts all individual SKUs, quantities, and prices automatically.
   - **Rate-Spike Detection:** Instantly cross-references prices with historical SQL records to alert the merchant if a distributor secretly increased wholesale prices.

3. 🧠 **Conversational Intelligence (End-to-End Voice QA)**
   No complex dashboards. Merchants can simply tap the microphone and ask *"Suresh ka kitna baaki hai?"* or *"Who is my best distributor?"* 
   - The system instantly transcribes the query, dynamically queries the database via LLM, and **speaks the answer back out loud** so the merchant doesn't even have to look at the screen.

4. ⚡ **Native Asynchronous Automation**
   Outbox events, vendor payouts, and WhatsApp/SMS alerts are routed asynchronously through an in-house Python native worker system—ensuring lightning-fast UI responses.

---

## 🏗️ The Technology Stack

We transitioned from local prototypes to a highly scalable cloud-native architecture:
- **Frontend:** React, Vite, Tailwind CSS (Clean, intuitive mobile-first UI)
- **Backend:** Python, FastAPI, SQLAlchemy (Lightning fast, strictly typed)
- **Database:** Supabase / PostgreSQL (Cloud-hosted with bulletproof Alembic migrations)
- **AI Models:** Groq (Llama 3), Google Vision (OCR), Sarvam AI (Indic Speech)

---

## 🚀 Getting Started (Developer Guide)

Follow these steps to run VyaparSetu locally on your computer.

### Prerequisites
- **Python** (3.11+)
- **Node.js**
- **A Supabase Project** (Free Tier is fine)

### 1. Configure the Environment
```bash
cd paytm-vyaparsetu
cp backend/.env.example backend/.env
```
*(Add your Supabase Connection Pooler URL, Sarvam, Groq, and Google Vision API keys in the `.env` file).*

### 2. Setup the Cloud Database
We use Alembic to automatically build the Supabase database. Open a terminal in the `paytm-vyaparsetu/backend` folder:
```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed_demo
```
*(Your cloud database is now fully built and populated with demo data).*

### 3. Start the Backend API
In the same backend terminal:
```bash
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

🎉 **You're all set!** Open the frontend link in your browser to experience VyaparSetu!

---

## 📚 Deep Dive
If you want to understand the system design further, check out the inner `paytm-vyaparsetu/README.md` which breaks down the specific inner workings of the `backend/` and `project/` folders.
