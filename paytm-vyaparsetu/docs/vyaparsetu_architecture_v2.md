# Paytm VyaparSetu System Architecture (Native PostgreSQL)

This architecture reflects the updated, high-performance production pipeline operating entirely on local infrastructure, bypassing legacy external vector databases or graph engines. All queries, extraction, and ledger math are grounded firmly in ACID-compliant SQLAlchemy models.

```mermaid
flowchart TD
    %% Base Infrastructure
    subgraph Storage["Native PostgreSQL DB"]
        SQL[(SQLAlchemy\nModels)]
        TBL1[merchants / customers]
        TBL2[ledger_transactions]
        TBL3[invoices / line_items]
        TBL4[settlement_daily_rollups]
        TBL5[insight_cache / outbox_events]
        SQL --- TRL
        TRL --- TBL1 & TBL2 & TBL3 & TBL4 & TBL5
    end

    %% Pipeline 1: Voice Khata
    subgraph Pipeline1["1. Conversational Voice Khata (< 500ms)"]
        V_IN((Voice Input\nHinglish/Vernacular))
        STT[Sarvam STT\n'Saaras']
        LLM1[Groq Llama-3.1-8B\nStrict Pydantic JSON]
        SQL_TXN{Entity Resolve &\nACID DB Commit}
        TTS[Sarvam TTS\n'Bulbul']
        OUTBOX[Outbox Event\nWhatsApp Follow-up]

        V_IN --> STT --> LLM1 --> SQL_TXN
        SQL_TXN -->|Commit ledger_transactions| Storage
        SQL_TXN --> TTS --> V_OUT((Audio Output\nUpdated Balance))
        SQL_TXN --> OUTBOX
    end

    %% Pipeline 2: Challan Lens
    subgraph Pipeline2["2. Smart Delivery Challan Lens (< 3.5s)"]
        C_IN((Challan Photo))
        OCR[Google Vision OCR]
        V_LLM[Groq Vision\nChallanExtractionResult]
        SKU_RES[SKU Resolution &\nNormalized Identifier]
        RATE_AUDIT{Rate-Spike Audit\nDB Query}
        PAY_CALC[Payout Computation\nDaily Rollups]

        C_IN --> OCR --> V_LLM --> SKU_RES
        SKU_RES -->|Lookup previous unit_price| Storage
        SKU_RES --> RATE_AUDIT
        RATE_AUDIT -->|Alert if spiked| Storage
        RATE_AUDIT --> PAY_CALC
        PAY_CALC -->|Compare against settlement| Storage
    end

    %% Pipeline 3: Operational Q&A
    subgraph Pipeline3["3. Grounded Operational Q&A (< 1.2s)"]
        QA_IN((Merchant Query))
        ROUTER{Intent Router\nSLM / Rule-based}
        
        CACHE{Check\ninsight_cache}
        SQL_AGG[SQL Aggregation\nExact Balances]
        SQL_HIS[SQL History\nTrends/Rates]
        LLM2[Groq LLM\nStrict Grounding]
        QA_OUT((Synthesized\nResponse))

        QA_IN --> ROUTER
        ROUTER --> CACHE
        
        %% Cache Flow
        CACHE -->|Miss| ROUTER_FWD
        CACHE -->|Hit| QA_OUT
        
        %% Category A (Exact Balance)
        ROUTER -- Category A --> SQL_AGG
        SQL_AGG -->|Query customers & ledger| Storage
        SQL_AGG --> QA_OUT
        
        %% Category B (Historical Trends)
        ROUTER -- Category B --> SQL_HIS
        SQL_HIS -->|Query invoices & items| Storage
        SQL_HIS --> LLM2
        LLM2 -->|Save Answer| CACHE
        LLM2 --> QA_OUT
    end
```

### Architectural Principles Enforced:
*   **No Hallucinations:** The LLM generates natural language exclusively from injected SQL row data. If SQL returns an empty set, the fallback behavior is triggered (`"Mere paas iski jaankari nahi hai"`).
*   **Zero-Overhead Q&A:** Explicit exact queries (like pending balance) hit SQL native aggregates (`SUM(CASE WHEN...)`) and bypass the LLM completely for maximum speed.
*   **Fast Extraction:** Voice transactions use small, blazing fast models (Groq Llama-3.1-8B) to map messy vernacular audio strictly to Pydantic objects.
*   **Auditable:** Every piece of data lives on-premise in the relational PostgreSQL database with strong constraints, foreign keys, and indexes.
