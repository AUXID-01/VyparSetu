# Paytm VyaparSetu — PostgreSQL Operations & Maintenance Guide

This document is a developer reference guide for managing, querying, inspecting, cleaning, and seeding the local PostgreSQL database stack running inside Docker.

---

## 1. Quick Access & Docker CLI Commands

### Container Status & Health
Inspect the running `vyaparsetu_postgres` container and healthcheck status:
```powershell
docker compose ps
# OR
docker ps -f name=vyaparsetu_postgres
```

### Direct `psql` Terminal Access
Open an interactive `psql` session inside the running container with a single command:
```powershell
docker exec -it vyaparsetu_postgres psql -U vyapar_user -d vyaparsetu_db
```

### Common `psql` Meta-Commands Cheatsheet

| Command | Action |
|---|---|
| `\dt` | List all 10 schema tables |
| `\d <table>` | Describe table columns, data types, foreign keys, and indexes (e.g. `\d customers`) |
| `\x` | Toggle expanded auto-formatted view (useful for reading long JSONB `outbox_events.payload`) |
| `\l` | List all databases |
| `\du` | List database roles/users |
| `\q` | Exit `psql` prompt |

---

## 2. Inspecting Live Tables (GUI vs CLI)

### GUI Connection Parameters
Connect using your preferred visual database client (**DBeaver**, **TablePlus**, **Postico**, or **VS Code Database Client Extension**):

| Parameter | Value |
|---|---|
| **Host** | `localhost` |
| **Port** | `5432` |
| **User** | `vyapar_user` |
| **Password** | `vyapar_pass` |
| **Database** | `vyaparsetu_db` |
| **SSL Mode** | `disable` |

---

### Key Sanity Check SQL Queries

Run these queries inside `psql` or your GUI tool to verify database logic:

#### 1. Check Customer Identity Resolution (`canonical_key` dedup)
Verifies that names like `"Suresh"` and `"suresh"` resolve to a single `canonical_key`:
```sql
SELECT customer_id, merchant_id, display_name, canonical_key, phone, created_at 
FROM customers 
ORDER BY created_at DESC;
```

#### 2. Check Ledger Balances (Canonical Balance Math)
Sums ledger credit transactions per customer to verify total balance arithmetic:
```sql
SELECT 
    c.customer_id, 
    c.display_name, 
    SUM(CASE WHEN lt.txn_type = 'CREDIT_ADDED' THEN lt.amount ELSE -lt.amount END) AS total_due 
FROM ledger_transactions lt
JOIN customers c ON lt.customer_id = c.customer_id
GROUP BY c.customer_id, c.display_name;
```

#### 3. Inspect Pending Outbox Events (Async Bridge Status)
Inspects outbox events waiting for background n8n worker polling:
```sql
SELECT event_id, merchant_id, event_type, status, attempt_count, created_at, payload 
FROM outbox_events 
WHERE status = 'PENDING' 
ORDER BY created_at ASC;
```

---

## 3. DB Operations & Clean Slate Commands

### Soft Reset: Truncate All Data (Keep Schema Intact)
To clear all demo/test data instantly without recreating database tables:

```sql
TRUNCATE TABLE 
    ledger_transactions, 
    outbox_events, 
    invoice_line_items, 
    invoices, 
    customers, 
    distributors, 
    alerts, 
    insight_cache, 
    settlement_daily_rollups, 
    merchants 
CASCADE;
```

---

### Hard Reset: Wipe Docker Volume & Re-run Migrations
If you need a complete fresh start (wipes Docker volume and re-applies Alembic migrations from scratch):

```powershell
# 1. Stop containers and delete named volumes (-v)
docker compose down -v

# 2. Start a fresh database container
docker compose up -d db

# 3. Re-apply Alembic migrations to head
cd backend
python -m alembic upgrade head
```

---

## 4. How to Seed Mock Data via Code

A runnable helper script is located at [`backend/scripts/seed_sample.py`](file:///c:/VyaparSetu/VyparSetu/paytm-vyaparsetu/backend/scripts/seed_sample.py). It uses `db/session.py` and `core/ids.py` to programmatically provision a merchant, customer, credit transaction, and outbox event idempotently.

### Run Seeding Script
```powershell
cd paytm-vyaparsetu/backend
python scripts/seed_sample.py
```

### Expected Output
```text
[1/3] Creating sample merchant...
  -> Created Merchant: Gupta Provision Store (ID: mer_4c637a)
[2/3] Resolving customer (Suresh)...
  -> Created Customer: Suresh (ID: cus_cd5326)
[3/3] Logging sample credit transaction & outbox event...
  -> Created Ledger Txn: txn_b811a2 (Amount: INR 240.00)
  -> Created Outbox Event: obx_e831a5 (Status: PENDING)

Demo data seeded successfully!
```
