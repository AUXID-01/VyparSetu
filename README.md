# Paytm VyaparSetu v2

**Intelligent Merchant Operations & Ledger Management**

## 👋 Welcome to VyaparSetu!

If you are a beginner or new to this project, you are in the right place! 

**Paytm VyaparSetu v2** is a next-generation merchant operations platform. It is designed to help merchants (shop owners, businesses) manage their ledgers, automate workflows, and get intelligent insights into their business—all through a lightning-fast and easy-to-use interface.

### 🚨 The Problem: Life of a "Kirana Wala" (Shop Owner)

To understand why we built VyaparSetu, imagine the daily struggles of an Indian local grocery store owner (a *Kirana wala*):
- 📝 **The "Udhaar" (Credit) Mess:** They manage customer credit in physical notebooks (Bahi Khata). Writing down every transaction during peak rush hours is slow, notebooks get lost or damaged, and handwriting issues lead to disputes.
- 📦 **Manual Bill Entry:** When vendors deliver goods, they hand over physical paper bills (Challans). The shop owner has to manually type hundreds of items into their system to update inventory and pricing—a massive daily time sink.
- 📉 **Hidden Price Hikes:** Because they process so many items manually, they often miss when a vendor secretly increases the wholesale rate of an item. This eats directly into their profit margins.
- ⏳ **End-of-Day Exhaustion:** After standing at the counter for 12+ hours, they still have to manually message customers for pending payments and figure out which vendors to pay the next day.

VyaparSetu was built to solve exactly these problems by introducing AI automation into their daily workflow, without slowing them down.

### 🤔 What does it do? (Key Features)

- 🎙️ **Voice-Powered Ledger:** Log credits and update customer balances simply by speaking. VyaparSetu instantly processes voice input (in Hindi/Hinglish) into structured ledger entries.
- 📄 **Automated Challan Digitization:** Upload physical challans (invoices) for instant extraction, validation, and digitization, drastically reducing manual data entry.
- 🧠 **Intelligent Business Insights:** Ask natural language questions about your business and receive synthesized, actionable answers. The system also automatically audits invoices for rate spikes and discrepancies.
- ⚡ **Automated Workflows:**
  - **Instant Payment Links:** Automatically dispatch UPI payment links to customers via WhatsApp or SMS.
  - **Vendor Payouts:** Automated, conditional payouts to vendors with built-in success/failure handling.
  - **Smart Alerts:** Real-time notifications for critical events like sudden rate spikes or low balances.

---

## 🏗️ Codebase Architecture & Tech Stack

VyaparSetu is built with a focus on speed and reliability. It is divided into two main layers:
1. **The Synchronous Core (Source of Truth):** Real-time operations that the merchant interacts with, ensuring zero latency.
2. **The Asynchronous Intelligence Layer:** Complex, time-consuming operations (AI reasoning, WhatsApp/SMS dispatch) handled quietly in the background without blocking the user.

### Tech Stack
- **Frontend:** React, Vite, Tailwind CSS, TypeScript
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic (for database migrations)
- **Database:** PostgreSQL (running via Docker)
- **AI Integrations:** Sarvam AI (Speech-to-Text / Text-to-Speech), Document AI (Challan OCR), Cognee (Knowledge Graph/Insights), n8n (Orchestrator for Webhooks)

---

## 📂 Directory Structure

Here is a simple map of the project to help you navigate:

```text
VparSetu/
├── README.md                      # You are here!
├── paytm-vyaparsetu/              # Main application code
│   ├── backend/                   # Python FastAPI backend
│   │   ├── api/                   # API Endpoints (routes for frontend to call)
│   │   ├── db/                    # Database models and queries
│   │   ├── memory/                # AI intelligence and background tasks
│   │   ├── services/              # Core business logic
│   │   ├── mock_services/         # Standalone mock services (e.g., Paytm Payouts simulator)
│   │   └── tests/                 # Automated tests
│   ├── project/                   # Frontend React + Vite Application
│   │   ├── src/                   # React components and pages
│   │   └── package.json           # Frontend dependencies
│   ├── deploy/                    # Dockerfiles and deployment scripts
│   ├── docs/                      # Extensive guides and documentation
│   └── docker-compose.yml         # Defines the PostgreSQL database container
```

---

## 🚀 Getting Started (Beginner Friendly)

Want to run VyaparSetu on your local machine? Follow these simple steps.

### Prerequisites
Make sure you have installed:
- **Python** (3.11 or higher)
- **Node.js** (for running the frontend)
- **Docker Desktop** (for running the database)
- **Git**

### Step 1: Clone and Configure Environment
1. Open your terminal and navigate to the main folder:
   ```bash
   cd paytm-vyaparsetu
   ```
2. Copy the example environment variables file to create your own configuration:
   ```bash
   cp .env.example .env
   ```
3. Open the `.env` file and add your **Sarvam API Key** (`SARVAM_API_KEY=...`).

### Step 2: Start the Database (PostgreSQL)
We use Docker to easily spin up a database.
1. Run the database container in the background:
   ```bash
   docker compose up -d db
   ```

### Step 3: Run the Backend (Python FastAPI)
1. Navigate to the backend folder (if not already inside `paytm-vyaparsetu`):
   ```bash
   cd paytm-vyaparsetu
   ```
2. Create and activate a virtual environment (this keeps Python packages isolated):
   - **Windows:** `python -m venv venv` then `.\venv\Scripts\Activate.ps1`
   - **Mac/Linux:** `python3 -m venv venv` then `source venv/bin/activate`
3. Install all required backend packages:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Run database migrations to set up the tables:
   ```bash
   cd backend
   alembic upgrade head
   cd ..
   ```
5. Start the backend API server:
   ```bash
   uvicorn backend.main:app --reload
   ```
   *Your backend API will now be running on http://localhost:8000*

### Step 4: Run the Frontend (React Application)
Open a **new** terminal window (so you don't stop the backend).
1. Navigate to the frontend directory:
   ```bash
   cd paytm-vyaparsetu/project
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   *Your frontend interface will now be running (usually on http://localhost:5173).*

🎉 **You're all set!** Open the frontend URL in your browser to explore VyaparSetu.

---

## 📚 Further Reading

If you want to dive deeper into specific parts of the project, check out the dedicated documentation inside `paytm-vyaparsetu/docs/`:
- **[SETUP_GUIDE.md](paytm-vyaparsetu/docs/SETUP_GUIDE.md)** — Detailed installation and troubleshooting.
- **[CHALLAN_SCHEMA_MIGRATION_GUIDE.md](paytm-vyaparsetu/docs/CHALLAN_SCHEMA_MIGRATION_GUIDE.md)** — How challans (invoices) are digitized and stored.
