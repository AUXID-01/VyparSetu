# Paytm VyaparSetu — Master Schema & API Contract (v1)

*This is the single source of truth for every name, field, and endpoint in the system. Once frontend build starts, nothing in here should change casually — if a name needs to change, update this doc first, then code, so backend and frontend never drift apart.*

---

## 0. How to use this document

- Section 1 = the naming rules everything else follows. Read this once, refer back when unsure.
- Section 2 = the database. This is what actually persists.
- Section 3 = every API endpoint, grouped by feature. This is the contract between frontend and backend.
- Section 4 = Cognee dataset/ontology setup, plus how to spend your credits well.
- Section 5 = n8n webhook contract.
- Section 6 = a cheat sheet mapping each UI screen directly to the endpoints and fields it needs — hand this to whoever's building in Bolt/Lovable.
- Section 7 = every enum used anywhere in the system, in one place, so no two files invent different status strings for the same thing.

---

## 1. Global naming conventions

**IDs** — every entity gets a short, prefixed, human-readable ID, not a raw UUID. Prefixes make logs and debugging instantly readable.

| Entity | Prefix | Example |
|---|---|---|
| Merchant | `mer_` | `mer_a1b2c3` |
| Customer | `cus_` | `cus_7f3d21` |
| Distributor | `dis_` | `dis_9k2m01` |
| Ledger transaction | `txn_` | `txn_8f3ac1` |
| Invoice | `inv_` | `inv_44d1e0` |
| Invoice line item | `lin_` | `lin_02af9c` |
| Outbox event | `obx_` | `obx_e91a0b` |
| Alert | `alt_` | `alt_c02f11` |
| Settlement rollup | `set_` | `set_2026-09-16_mer_a1b2c3` (date + merchant, deterministic, not random) |

Generate as `f"{prefix}{uuid4().hex[:6]}"` — 6 hex chars is enough entropy for hackathon scale and stays short in logs.

**Field naming**
- All fields `snake_case`, no camelCase anywhere — backend, database, and API all match exactly, so nothing needs translation at any hop.
- Every timestamp field ends in `_at` and is stored/transmitted as ISO 8601 UTC (`2026-09-16T14:32:00Z`), never a Unix epoch, never local time.
- Every boolean field starts with `is_` or `has_` (`is_paid`, `has_phone`).
- Every foreign key field is exactly `{referenced_entity}_id` (`customer_id`, `merchant_id`) — never abbreviated differently in different tables.
- Every enum/status field is an `UPPER_SNAKE_CASE` string, not an integer code — integers require a lookup table to be human-readable, strings don't. Full enum list in Section 7.

**API conventions**
- Base path: `/api/v1/...` — version in the URL from day one, so a v2 later never breaks the hackathon build.
- All request/response bodies are flat where possible, nested only where the data is genuinely hierarchical (e.g. an invoice's line items). This mirrors the "flat JSON to n8n" rule from the architecture doc — the shallower the payload, the fewer places for a frontend/backend mismatch to hide.
- Every response is wrapped in a standard envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```
```json
{
  "success": false,
  "data": null,
  "error": { "code": "CUSTOMER_NOT_FOUND", "message": "No customer found with this id for this merchant." }
}
```
This means the frontend only ever needs one pattern for every single API call: check `success`, then read `data` or `error`. Error `code` values are also listed in Section 7, so the frontend can branch on code, not on parsing message text.

- Auth: every request from the frontend carries `Authorization: Bearer <merchant_session_token>`. Every internal callback from n8n carries a separate fixed header, `X-Internal-Token: <shared_secret>`, so internal callback endpoints can never be hit by anything pretending to be the frontend.

---

## 2. PostgreSQL schema (full DDL)

```sql
-- ============================================================
-- merchants: the root of every other table. One row per shop.
-- ============================================================
CREATE TABLE merchants (
    merchant_id     TEXT PRIMARY KEY,           -- 'mer_xxxxxx'
    shop_name       TEXT NOT NULL,
    owner_name      TEXT NOT NULL,
    phone           TEXT NOT NULL UNIQUE,
    cognee_dataset  TEXT NOT NULL UNIQUE,       -- e.g. 'merchant_mer_xxxxxx' — set once at onboarding, never changes
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- customers: people who buy on credit. Scoped to one merchant —
-- the same phone number at two different shops is two different rows,
-- deliberately, since credit relationships don't cross shops.
-- ============================================================
CREATE TABLE customers (
    customer_id     TEXT PRIMARY KEY,           -- 'cus_xxxxxx'
    merchant_id     TEXT NOT NULL REFERENCES merchants(merchant_id),
    display_name    TEXT NOT NULL,              -- exactly as the merchant said it, for showing on screen
    canonical_key   TEXT NOT NULL,              -- phone number if known, else lower(trim(display_name)) — THIS is what
                                                 -- prevents the "Suresh" vs "suresh" duplicate-entity problem found in testing
    phone           TEXT,                       -- nullable — not every customer has a phone on file
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (merchant_id, canonical_key)          -- this constraint is the actual dedup enforcement
);

-- ============================================================
-- distributors: suppliers who deliver stock.
-- ============================================================
CREATE TABLE distributors (
    distributor_id  TEXT PRIMARY KEY,           -- 'dis_xxxxxx'
    merchant_id     TEXT NOT NULL REFERENCES merchants(merchant_id),
    name            TEXT NOT NULL,
    upi_id          TEXT,
    canonical_key   TEXT NOT NULL,              -- same dedup principle as customers
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (merchant_id, canonical_key)
);

-- ============================================================
-- ledger_transactions: THE source of truth for money. Every credit
-- given or paid back is one immutable row here. Balances are always
-- computed by summing this table — never stored as a separately
-- mutable number, so they can never drift out of sync with history.
-- ============================================================
CREATE TABLE ledger_transactions (
    txn_id          TEXT PRIMARY KEY,           -- 'txn_xxxxxx'
    merchant_id     TEXT NOT NULL REFERENCES merchants(merchant_id),
    customer_id     TEXT NOT NULL REFERENCES customers(customer_id),
    amount          NUMERIC(10,2) NOT NULL,     -- always positive; direction comes from txn_type
    txn_type        TEXT NOT NULL,              -- 'CREDIT_ADDED' | 'CREDIT_PAID' — see Section 7
    items           TEXT[] NOT NULL DEFAULT '{}',  -- e.g. {'Dahi','Refined Oil'} — descriptive only, not inventory-tracked
    source          TEXT NOT NULL,              -- 'VOICE' | 'MANUAL' — see Section 7
    extraction_confidence NUMERIC(3,2),         -- nullable; only set when source = 'VOICE'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ledger_customer ON ledger_transactions (merchant_id, customer_id);
CREATE INDEX idx_ledger_date ON ledger_transactions (merchant_id, created_at);

-- ============================================================
-- invoices: one row per confirmed delivery challan.
-- Created only AFTER merchant confirms the vision-extracted data —
-- never written straight from raw OCR output.
-- ============================================================
CREATE TABLE invoices (
    invoice_id      TEXT PRIMARY KEY,           -- 'inv_xxxxxx'
    merchant_id     TEXT NOT NULL REFERENCES merchants(merchant_id),
    distributor_id  TEXT NOT NULL REFERENCES distributors(distributor_id),
    invoice_date    DATE NOT NULL,
    total_amount    NUMERIC(10,2) NOT NULL,
    is_paid         BOOLEAN NOT NULL DEFAULT false,
    paid_at         TIMESTAMPTZ,                -- set by the n8n payout callback
    payout_reference TEXT,                      -- set by the n8n payout callback on success
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- invoice_line_items: individual SKUs within an invoice.
-- This is what the instant rate-spike check compares against —
-- a plain SQL lookup, NOT a Cognee query (see Section 4 for why).
-- ============================================================
CREATE TABLE invoice_line_items (
    line_item_id    TEXT PRIMARY KEY,           -- 'lin_xxxxxx'
    invoice_id      TEXT NOT NULL REFERENCES invoices(invoice_id),
    distributor_id  TEXT NOT NULL REFERENCES distributors(distributor_id),  -- denormalized on purpose,
                                                 -- so the rate-spike query never needs a join through invoices
    sku             TEXT NOT NULL,              -- e.g. 'Dahi 200g pouch' — normalize casing/spacing on write
    quantity        INT NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL
);
CREATE INDEX idx_line_item_rate_lookup ON invoice_line_items (distributor_id, sku, invoice_id);

-- ============================================================
-- settlement_daily_rollups: one row per merchant per day.
-- Precomputed and stored — never recalculated live — so the same
-- question about the same day always returns the identical answer.
-- ============================================================
CREATE TABLE settlement_daily_rollups (
    rollup_id            TEXT PRIMARY KEY,      -- 'set_YYYY-MM-DD_mer_xxxxxx'
    merchant_id          TEXT NOT NULL REFERENCES merchants(merchant_id),
    rollup_date          DATE NOT NULL,
    upi_collection_total NUMERIC(10,2) NOT NULL DEFAULT 0,
    payout_total         NUMERIC(10,2) NOT NULL DEFAULT 0,
    net_balance          NUMERIC(10,2) NOT NULL DEFAULT 0,
    computed_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (merchant_id, rollup_date)
);

-- ============================================================
-- outbox_events: the bridge to Cognee. See v2 architecture doc
-- for the full pattern. status transitions PENDING -> SYNCED | FAILED.
-- ============================================================
CREATE TABLE outbox_events (
    event_id        TEXT PRIMARY KEY,           -- 'obx_xxxxxx' — this IS the idempotency key
    merchant_id     TEXT NOT NULL REFERENCES merchants(merchant_id),
    event_type      TEXT NOT NULL,              -- 'CREDIT_ADDED' | 'INVOICE_CREATED' | 'SETTLEMENT_ROLLUP' — Section 7
    payload         JSONB NOT NULL,             -- canonical IDs only, never raw names — see Section 4
    status          TEXT NOT NULL DEFAULT 'PENDING',
    attempt_count   INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    synced_at       TIMESTAMPTZ
);
CREATE INDEX idx_outbox_pending ON outbox_events (status, created_at) WHERE status = 'PENDING';

-- ============================================================
-- insight_cache: precomputed Cognee-derived answers, so the UI
-- and grounded Q&A NEVER call cognee.search() live on a request path.
-- ============================================================
CREATE TABLE insight_cache (
    cache_key       TEXT PRIMARY KEY,           -- e.g. 'rate_trend_mer_xxxxxx_dis_xxxxxx'
    merchant_id     TEXT NOT NULL REFERENCES merchants(merchant_id),
    insight_type    TEXT NOT NULL,              -- 'RATE_TREND' | 'QA_ANSWER' | 'SUPPLIER_SUMMARY' — Section 7
    result          JSONB NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    stale_after     TIMESTAMPTZ NOT NULL        -- UI shows "insights syncing" if now() > stale_after and a refresh is pending
);

-- ============================================================
-- alerts: rate-spike / low-balance notices shown to the merchant.
-- ============================================================
CREATE TABLE alerts (
    alert_id        TEXT PRIMARY KEY,           -- 'alt_xxxxxx'
    merchant_id     TEXT NOT NULL REFERENCES merchants(merchant_id),
    alert_type      TEXT NOT NULL,              -- 'RATE_SPIKE' | 'LOW_BALANCE' — Section 7
    details         JSONB NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 3. API endpoints

Every endpoint below states: method + path, auth, request shape, response shape (inside the `data` envelope from Section 1), which tables it touches, and whether it's purely synchronous or also fires a background/async side effect.

### 3.1 Merchant domain

**`POST /api/v1/merchants`** — onboard a new merchant *(also triggers the n8n Merchant Onboarding workflow)*
- Auth: none (signup)
- Request: `{ "shop_name": "Gupta Provision Store", "owner_name": "Ramesh Gupta", "phone": "+919876543210" }`
- Response: `{ "merchant_id": "mer_a1b2c3", "cognee_dataset": "merchant_mer_a1b2c3", "session_token": "..." }`
- Tables: `merchants` (insert)
- Async: fires webhook to n8n Merchant Onboarding workflow, which provisions the Cognee dataset

**`GET /api/v1/merchants/{merchant_id}`**
- Response: full merchant profile, no financial data (that's the query domain below)

### 3.2 Voice domain

**`POST /api/v1/voice/transcribe`**
- Request: multipart audio file
- Response: `{ "transcript": "...", "language_detected": "hi-en" }`
- Tables: none — pure passthrough to Sarvam STT, nothing persisted yet
- Sync only

**`POST /api/v1/voice/log-credit`**
- Request: `{ "merchant_id": "mer_a1b2c3", "raw_transcript": "...", "extracted": { "customer_name": "Suresh", "amount": 240, "items": ["Dahi","Refined Oil"], "confidence": 0.91 } }`
- Response: `{ "txn_id": "txn_8f3ac1", "customer_id": "cus_7f3d21", "new_balance": 300.00, "confirmation_audio_text": "Suresh ji ke khate mein do sau chalis rupaye jod diye gaye hain." }`
- Tables: resolves/creates `customers` row (via `canonical_key`), inserts `ledger_transactions`, inserts `outbox_events`
- Sync: the ledger write and balance response are instant. Async: the outbox row is picked up later by n8n, and a Payment Link Dispatch webhook fires right after this response is returned (fire-and-forget, doesn't block the response)

### 3.3 Challan domain

**`POST /api/v1/challan/extract`**
- Request: multipart image file + `merchant_id`
- Response: `{ "distributor_name_guess": "Amul Distributor - Sector 4", "line_items": [ { "sku": "Dahi 200g pouch", "quantity": 50, "unit_price": 28.50 } ], "total_amount": 3850, "extraction_confidence": 0.83 }`
- Tables: none yet — this is the "please confirm" step, nothing persisted until `/challan/confirm`
- Sync only

**`POST /api/v1/challan/confirm`**
- Request: the (merchant-edited, if needed) version of the above extraction, plus `merchant_id`
- Response: `{ "invoice_id": "inv_44d1e0", "rate_alerts": [ { "sku": "Dahi 200g pouch", "previous_price": 27.00, "current_price": 28.50, "delta": 1.50 } ], "settlement": { "invoice_total": 3850, "balance_available": 5200, "remaining_after": 1350 } }`
- Tables: resolves/creates `distributors`, inserts `invoices`, inserts `invoice_line_items`, inserts `outbox_events`
- **This is the instant rate-spike answer** — `rate_alerts` is computed via a plain SQL lookup against `invoice_line_items` (Section 2), returned in the same response, no waiting
- Sync only for the alert; async outbox write for Cognee happens after

**`POST /api/v1/challan/settle`**
- Request: `{ "invoice_id": "inv_44d1e0" }`
- Response: `{ "payout_status": "INITIATED" }`
- Tables: none directly — fires the n8n Vendor Payout webhook
- Async: `is_paid`/`paid_at`/`payout_reference` on `invoices` are updated later by the n8n callback endpoint (Section 3.5)

### 3.4 Query domain

**`GET /api/v1/query/customer-due/{customer_id}`**
- Response: `{ "customer_id": "cus_7f3d21", "display_name": "Suresh", "total_due": 300.00 }`
- Tables: `SELECT sum(...) FROM ledger_transactions` — always live SQL, never cached, since this must always be exact
- Sync only, <5ms target

**`GET /api/v1/query/daily-summary?merchant_id=mer_a1b2c3&date=2026-09-16`**
- Response: the `settlement_daily_rollups` row for that date
- Tables: reads `settlement_daily_rollups` (precomputed) if it exists, else computes live from `ledger_transactions`/`invoices` and writes it
- Sync only

**`POST /api/v1/query/ask`** — the grounded Q&A / "ask me anything" feature
- Request: `{ "merchant_id": "mer_a1b2c3", "question": "How has Amul's pricing trended this month?" }`
- Response: `{ "answer": "...", "source": "CACHE" }` or `{ "answer": "...", "source": "LIVE", "generated_in_ms": 6200 }`
- Tables: checks `insight_cache` first by a derived `cache_key`; if fresh, returns instantly; if stale/missing, calls Cognee live **only here**, and stores the result back into `insight_cache` for next time
- This is the one endpoint in the whole system allowed to be slow — and it tells the frontend which mode it was (`CACHE` vs `LIVE`) so the UI can show a spinner honestly instead of faking instant speed

### 3.5 Internal callback domain (n8n → backend only, `X-Internal-Token` required)

**`POST /api/v1/internal/outbox/callback`**
- Request: `{ "event_id": "obx_e91a0b", "status": "SYNCED" }`
- Tables: updates `outbox_events.status`/`synced_at`

**`POST /api/v1/internal/payout/callback`**
- Request: `{ "invoice_id": "inv_44d1e0", "paid": true, "payout_reference": "PAYTM-REF-123" }` or `{ "invoice_id": "...", "paid": false, "failure_reason": "INSUFFICIENT_FUNDS" }`
- Tables: updates `invoices.is_paid`/`paid_at`/`payout_reference`

---

## 4. Cognee schema, dataset conventions, and using your credits well

**Dataset naming** — one dataset per merchant, named exactly as stored in `merchants.cognee_dataset` (`merchant_mer_xxxxxx`), plus one separate `dev_sandbox` dataset used only during development so test runs never pollute or burn credits against a "real" merchant dataset you intend to demo with. Before judging, do a final clean push into a fresh demo-only dataset so the graph judges see isn't cluttered with weeks of test noise.

**Enforce an ontology instead of free-form extraction** — since you have credits to spare, use Cognee's custom ontology/schema support to lock down exactly which node and edge types `cognify()` is allowed to create, rather than letting it infer freely from text. This is the single biggest lever you have against the entity-splitting and non-deterministic-topology problems you already found:

```python
# memory/cognee_ontology.py
"""
Passed to cognee.cognify(ontology=...) so extraction is constrained to
exactly these types — no inferred entity types, no surprise topology drift
between runs.
"""
from pydantic import BaseModel

class Customer(BaseModel):
    customer_id: str      # always the canonical Postgres ID, never a raw name
    merchant_id: str
    display_name: str

class Transaction(BaseModel):
    txn_id: str
    customer_id: str
    amount: float
    txn_type: str

class Distributor(BaseModel):
    distributor_id: str
    merchant_id: str
    name: str

class Invoice(BaseModel):
    invoice_id: str
    distributor_id: str
    invoice_date: str
    total_amount: float

class LineItem(BaseModel):
    invoice_id: str
    sku: str
    quantity: int
    unit_price: float
```

**Payload contract into Cognee (via the outbox)** — only ever send the canonical objects above, built from Postgres IDs, never a raw transcript or raw OCR text. This is what closes the "Suresh vs suresh" gap for good: Cognee physically cannot invent a duplicate customer node if it only ever receives an already-deduplicated `customer_id`.

**Batch instead of one-event-at-a-time** — since `add()`/`cognify()` each cost ~3–4 seconds and (per your note) you're budgeting all your Cognee credits for this hackathon specifically, have the n8n Outbox Poller batch, say, 5–10 pending events per run into a single `cognify()` call rather than one call per event. Fewer, larger calls both stretches your credits further and reduces total indexing overhead.

**Where to actually spend the credits for maximum demo impact:**
1. The rate-audit ontology above (core to your pitch, cheap to run since it's simple structured data)
2. The grounded Q&A endpoint (`/query/ask`) — this is your most "wow" feature for judges, worth reserving credits for live queries during the actual demo rather than only pre-cached ones
3. A nightly (or pre-demo, on-demand) "supplier summary" batch job — a stretch feature: one Cognee query per distributor that summarizes pricing behavior over the full history, cached into `insight_cache` with `insight_type = 'SUPPLIER_SUMMARY'` — cheap to add given the ontology is already enforced, and gives you a second, distinct grounded-answer demo moment beyond the single rate-spike alert

---

## 5. n8n webhook contract

| Workflow | Path (on n8n Cloud) | Payload (flat JSON only) |
|---|---|---|
| Payment Link Dispatch | `/webhook/payment-link` | `{ "customer_phone", "amount", "merchant_name", "upi_link" }` |
| Vendor Payout | `/webhook/vendor-payout` | `{ "invoice_id", "distributor_upi_id", "amount" }` |
| Alert Dispatch | `/webhook/alert-dispatch` | `{ "merchant_id", "alert_type", "details_json" }` (stringified, since alert `details` is itself a small object) |
| Merchant Onboarding | `/webhook/merchant-onboarding` | `{ "merchant_id", "shop_name", "phone", "cognee_dataset" }` |
| Outbox Poller (n8n → FastAPI) | n8n calls `GET /api/v1/internal/outbox/pending`, not a webhook | reads pending rows directly |

Every webhook call from FastAPI includes header `X-Internal-Token: <shared_secret>` (the same one n8n uses to call back into `/api/v1/internal/*`), so the trust boundary is symmetric in both directions.

---

## 6. Frontend ↔ backend cheat sheet (for whoever builds the UI in Bolt/Lovable)

| Screen | Calls | Key fields to render |
|---|---|---|
| Voice recorder / khata entry | `POST /voice/transcribe` → `POST /voice/log-credit` | `new_balance`, `confirmation_audio_text` |
| Customer dues list | `GET /query/customer-due/{customer_id}` (per customer) | `display_name`, `total_due` |
| Challan upload | `POST /challan/extract` → (edit UI) → `POST /challan/confirm` | `rate_alerts[]`, `settlement.remaining_after` |
| Settlement/payout button | `POST /challan/settle` | `payout_status` (then poll invoice or listen for the async update) |
| Daily dashboard | `GET /query/daily-summary` | `upi_collection_total`, `payout_total`, `net_balance` |
| "Ask anything" box | `POST /query/ask` | `answer`, `source` (use `source` to decide whether to show a "thinking..." delay honestly) |
| Sync-status badge (any screen) | derived from `outbox_events.status` for that entity's `event_id` | shows "recorded" once `SYNCED`, "syncing" while `PENDING` |

Every field name in this table is exactly the JSON key from Section 3 — the frontend never needs to rename anything on the way in.

---

## 7. Master enum list (single source, do not redefine elsewhere)

| Enum | Values |
|---|---|
| `txn_type` | `CREDIT_ADDED`, `CREDIT_PAID` |
| `source` (ledger) | `VOICE`, `MANUAL` |
| `outbox status` | `PENDING`, `SYNCED`, `FAILED` |
| `event_type` (outbox) | `CREDIT_ADDED`, `INVOICE_CREATED`, `SETTLEMENT_ROLLUP` |
| `insight_type` | `RATE_TREND`, `QA_ANSWER`, `SUPPLIER_SUMMARY` |
| `alert_type` | `RATE_SPIKE`, `LOW_BALANCE` |
| `payout_status` (response only, not stored) | `INITIATED`, `SUCCEEDED`, `FAILED` |
| `query/ask source` | `CACHE`, `LIVE` |
| Error `code` values | `CUSTOMER_NOT_FOUND`, `MERCHANT_NOT_FOUND`, `INVOICE_NOT_FOUND`, `LOW_CONFIDENCE_EXTRACTION`, `DUPLICATE_MERCHANT_PHONE`, `INTERNAL_TOKEN_INVALID` |

---

## 8. Pre-requisites checklist before UI build starts

- [ ] Postgres schema (Section 2) created in a real dev database, not just this doc
- [ ] Cognee ontology file (Section 4) written and tested against at least one sample `cognify()` call
- [ ] `dev_sandbox` Cognee dataset created, separate from any future demo dataset
- [ ] n8n Cloud webhooks scaffolded (can be stubbed/empty at first) so their URLs exist and can be hardcoded into `.env` before frontend needs them
- [ ] Shared `X-Internal-Token` secret generated and placed in both FastAPI's and n8n's env/credentials
- [ ] Both partners have read Section 1 and agree not to deviate from the naming rules without updating this doc first
