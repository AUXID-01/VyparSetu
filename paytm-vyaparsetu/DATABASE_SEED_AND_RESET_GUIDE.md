# VyaparSetu: Database Seed and Reset Guide

This guide explains how to properly wipe and seed the PostgreSQL database for development, edge-case testing, and live demo presentations. We have explicitly abandoned "ad-hoc" database state testing in favor of deliberate, structured seeds to ensure deterministic and verifiable outcomes.

---

## 1. Wiping the Database

Before running any seed script, or anytime you suspect organic test data is interfering with your queries, you must completely wipe the database. 

Our wipe script (`wipe.sql`) safely executes a `TRUNCATE TABLE ... CASCADE` across all 12 core tables in the correct dependency order.

**Via Python CLI Wrapper (Recommended):**
```bash
cd backend
python -m scripts.reset_db
```
*You will be prompted to confirm the deletion. This connects via SQLAlchemy and executes the raw SQL.*

**Via Docker/Postgres CLI directly:**
```bash
docker exec -i vyaparsetu_postgres psql -U vyapar_user -d vyaparsetu_db < backend/scripts/wipe.sql
```

---

## 2. Dev Environment Seed (`seed_dev.py`)

**When to run this:**
Run this script while actively developing Phase 7 (Cognee Integration), Phase 8 (n8n Cloud Automation), and Phase 9 (End-to-End Testing).

**What it does:**
This script executes real repository and service functions (e.g., `customers_repo.resolve_or_create`) to authentically trigger Canonical ID Deduplication and queue `outbox_events` for n8n.

**The 3 Test Merchants Generated:**
1. **Merchant 1 (Baseline Clean Store):**
   - 2 customers, 1 distributor ("Amul Dairy").
   - 5 Ledger Transactions.
   - 2 Invoices with an orchestrated rate spike (Old: ₹27.00, New: ₹28.50) to test SQL `RATE_SPIKE` alert triggers.
2. **Merchant 2 (Dedup Stress Test Store):**
   - Programmatically tests deduplication by inserting "Suresh", "suresh", and " Suresh " and asserting that they all collapse into a single `customer_id`.
   - Performs similar deduplication assertions on Distributor names.
3. **Merchant 3 (Cross-Merchant Isolation Store):**
   - Injects the exact same distributor name ("Amul Dairy") and SKU ("Dahi 200g Pouch") as Merchant 1.
   - Used as a strict negative control to prove that Graph RAG and SQL queries never leak data across tenants.

**How to run:**
```bash
cd backend
python -m scripts.reset_db
python -m scripts.seed_dev
```

---

## 3. Demo Environment Seed (`seed_demo.py`)

**When to run this:**
Run this script *only* before a live demo rehearsal or the final judging presentation (Phase 10). It ensures a completely clean, cold-start state.

**What it does:**
It seeds exactly two merchants with perfectly curated data matching our pitch personas and financial values exactly.

**The 2 Demo Merchants Generated:**
1. **Ramesh Gupta (`mer_ramesh_gupta`):**
   - **Shop:** Gupta Provision Store
   - **Customer:** Suresh (₹240.00 Credit for Dahi & Refined Oil).
   - **Distributor:** Amul Distributor.
   - **Invoices:** Two curated invoices explicitly built to trigger a `+₹1.50` rate spike on "Dahi 200g Pouch". 
   - **Settlement Net Balance:** ₹2350.00 (upi: 6200, payout: 3850).
2. **Tukaram Shinde (`mer_tukaram_shinde`):**
   - **Shop:** Shinde Dairy & Bakery
   - Used purely as a clean secondary tenant for live proof of multi-tenant isolation.

**How to run:**
```bash
cd backend
python -m scripts.reset_db
python -m scripts.seed_demo
```

---

## Summary of Expected State

| Action | Total Merchants | Total Pending Outbox Events | Expected Rate Spike (Amul) | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| `python -m scripts.reset_db` | 0 | 0 | None | Cleanup |
| `python -m scripts.seed_dev` | 3 | 8 | +₹1.50 (Merchant 1) | Development / Stress Tests |
| `python -m scripts.seed_demo`| 2 | 1 | +₹1.50 (Ramesh) | Pitch / Live Demo |
