# Paytm VyaparSetu

## Folder Skeleton & Architecture Overview

```
paytm-vyaparsetu/
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml              # Local dev stack (db, backend, frontend, mock-paytm)
├── docker-compose.override.yml     # Local mounts & debug flags (gitignored)
│
├── deploy/                         # Production & container deployment assets
│   ├── docker/
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   └── Dockerfile.mock_paytm
│   ├── nginx/
│   │   └── nginx.conf              # Reverse proxy handling /api -> backend, / -> frontend
│   └── scripts/
│       ├── seed_db.sh              # Populates initial demo merchants & catalog
│       └── wait_for_postgres.sh
│
├── frontend/                       # Exported directly from Bolt.new / Lovable
│
└── backend/
    ├── main.py                     # FastAPI entrypoint & router aggregation
    ├── config.py                   # Pydantic BaseSettings (env, credentials, webhooks)
    ├── requirements.txt
    │
    ├── api/
    │   ├── __init__.py
    │   ├── deps.py                 # DB session injection, Auth & X-Internal-Token checks
    │   └── routes/
    │       ├── __init__.py
    │       ├── merchants.py        # Provisioning, profiles, Soundbox settings
    │       ├── voice.py            # POST /v1/voice/log-credit
    │       ├── challan.py          # POST /v1/challan/extract & confirm
    │       ├── query.py            # GET /v1/query/summary (strictly reads Postgres cache)
    │       ├── internal.py         # n8n hooks: /internal/outbox/pending, /synced
    │       └── health.py           # Container readiness & liveness probes
    │
    ├── db/
    │   ├── __init__.py             # Exports get_db session dependency
    │   ├── session.py              # SQLAlchemy engine & sessionmaker
    │   ├── models.py               # ORM mapping matching schema exactly
    │   ├── migrations/             # Alembic migration revisions
    │   └── repositories/           # Isolated data access objects (no business logic)
    │       ├── __init__.py
    │       ├── merchants_repo.py
    │       ├── customers_repo.py   # Identity resolution (phone -> customer_id)
    │       ├── ledger_repo.py      # Canonical balance math
    │       ├── invoices_repo.py    # SQL single-fact last-rate lookup
    │       ├── outbox_repo.py      # Transactional outbox pattern reads/writes
    │       ├── insight_cache_repo.py
    │       └── alerts_repo.py
    │
    ├── sarvam/                     # Indic Speech-to-Text & Text-to-Speech
    │   ├── __init__.py             # Façade: transcribe_audio(), synthesize_speech()
    │   ├── client.py
    │   ├── stt.py
    │   ├── tts.py
    │   └── tests/
    │
    ├── vision/                     # Document AI / Challan OCR
    │   ├── __init__.py             # Façade: extract_challan(image_bytes) -> dict
    │   ├── client.py
    │   ├── prompts.py
    │   └── tests/
    │
    ├── extraction/                 # Conversational entity parsing (Hindi/Hinglish)
    │   ├── __init__.py             # Façade: extract_entities(transcript) -> dict
    │   ├── client.py
    │   ├── prompts.py
    │   └── tests/
    │
    ├── memory/                     # Background Cognee intelligence layer
    │   ├── __init__.py             # Façade: remember_event(), ask_background_insights()
    │   ├── ontology.py             # Pydantic schemas for Cognee cognify()
    │   ├── graph_client.py
    │   ├── dataset_manager.py      # Isolated merchant_<id> provisioning
    │   ├── queries.py
    │   └── tests/
    │
    ├── orchestrator/               # n8n Cloud Webhook triggers & bridges
    │   ├── __init__.py             # Façade: dispatch_payment_link(), trigger_payout()
    │   ├── n8n_client.py
    │   ├── outbox_poller_support.py
    │   └── tests/
    │
    ├── services/                   # Business logic orchestrators (multi-package coordinators)
    │   ├── __init__.py
    │   ├── voice_service.py        # Audio -> Sarvam -> Extraction -> DB -> Outbox
    │   ├── challan_service.py      # Vision -> SQL Rate-Spike check -> Payout draft
    │   ├── query_service.py        # Cached summary fetch with stale fallback
    │   └── merchant_service.py
    │
    ├── core/                       # Shared platform primitives
    │   ├── __init__.py
    │   ├── ids.py                  # Prefixed ID generators (mer_, txn_, out_)
    │   ├── errors.py               # Custom exceptions & HTTP exception handlers
    │   ├── enums.py                # TransactionStatus, OutboxStatus, AlertType
    │   └── auth.py                 # Token validation
    │
    ├── mock_services/
    │   └── mock_paytm/             # Standalone service mimicking Paytm Payouts & Soundbox
    │       ├── __init__.py
    │       ├── main.py             # Tiny FastAPI app on port 8001
    │       └── requirements.txt
    │
    └── tests/
        ├── conftest.py
        └── test_integration_e2e.py # Counter-speed E2E tests (Voice & Challan fast-path)
```

## Key Architecture & Docker Strategy Notes

1. **Local Network Isolation**:
   In `docker-compose.yml`, `frontend`, `backend`, `postgres`, and `mock_paytm` run on a single bridge network (`vyaparsetu-net`).

2. **Port Allocation**:
   - `Frontend`: Port `3000`
   - `Backend API`: Port `8000`
   - `mock_paytm`: Port `8001` (Isolated microservice simulating Paytm Payouts & Soundbox core gateway without polluting main app routes).

3. **Outbox Reliability**:
   `n8n Cloud` reaches local/staged FastAPI instance via tunnel or hosted URL targeting `/api/v1/internal/outbox/pending`, pulling records cleanly out of `outbox_repo.py`.
