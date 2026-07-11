# Data Flow Diagram (DFD) — WATT-IF

**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## 1. Introduction

This document presents the Data Flow Diagrams for the WATT-IF system, illustrating how data moves between external entities, processes, and data stores at multiple levels of abstraction.

### DFD Notation

| Symbol | Meaning |
|--------|---------|
| **Rectangle** | External Entity (source/sink of data outside the system boundary) |
| **Circle / Rounded Rectangle** | Process (transforms or routes data) |
| **Open-ended Rectangle** | Data Store (persistent storage) |
| **Arrow →** | Data Flow (direction indicates flow of data) |

---

## 2. Context Diagram (Level 0)

The Level 0 DFD shows the entire WATT-IF system as a single process and its interactions with external entities.

### External Entities

| Entity | Description |
|--------|-------------|
| **User** | A registered household electricity consumer who interacts with the system via a web/PWA interface |
| **Meralco S3 Bucket** | Meralco's AWS S3 bucket (`meralcomain.s3.ap-southeast-1.amazonaws.com`) hosting PDF rate schedule documents |
| **Ollama LLM** | Local language model service (qwen3:1.7b) for generating natural-language answers via `/api/chat` endpoint |

### Level 0 Diagram

```
                                ┌─────────────────────┐
                                │ Meralco S3 Bucket   │
                                │ (Rate PDF Host)     │
                                └──────────┬──────────┘
                                           │ Rate Schedule PDF
                                           ▼
┌──────┐   Credentials/Data       ┌──────────────────────┐
│      │ ────────────────────►   │                      │
│      │                          │                      │
│      │   Forecasts/              │                      │
│ User │   Answers/                │      WATT-IF         │
│      │   Reports                 │      System          │
│      │ ◄────────────────────    │                      │
│      │                          │                      │
└──────┘                          │                      │
                                  │                      │   Prompt + Context    ┌──────────────┐
                                  │                      │ ────────────────────► │ Ollama LLM   │
                                  │                      │ ◄──────────────────── │ (qwen3:1.7b) │
                                  └──────────────────────┘   Streamed Tokens    └──────────────┘
```

### Level 0 Data Flows

| # | From | To | Data |
|---|------|----|------|
| 1 | User | WATT-IF System | Registration credentials, login credentials, CSV files, manual data entries, forecast requests (horizon), chat questions, user settings |
| 2 | WATT-IF System | User | JWT token, forecast results (kWh, price, 95% CI), SSE-streamed chat answers, data entries, health status, Meralco rate breakdown |
| 3 | Meralco S3 Bucket | WATT-IF System | PDF rate schedule document (monthly, per customer type) |
| 4 | WATT-IF System | Ollama LLM | System prompt + forecast context + EDA context + user question (JSON messages array) |
| 5 | Ollama LLM | WATT-IF System | Streamed answer tokens (chunked JSON via `/api/chat`) |

> **Note on weather/ENSO data:** The current system does not call Open-Meteo or NOAA APIs at runtime. All exogenous variables (temperature, humidity, rainfall, El Niño phase, holiday counts, etc.) are pre-populated in the uploaded CSV dataset and enriched via `FeatureEngineeringService` using Philippine climate priors (PAGASA Metro Manila normals) for future forecast months. No external weather API calls are made during operation.

---

## 3. Level 1 DFD

The Level 1 DFD decomposes the WATT-IF system into its major processes, mapped to actual system modules.

### Processes

| # | Process | System Module | Description |
|---|---------|---------------|-------------|
| 1.0 | User Authentication | `api/auth.py` | Manages user registration (`/auth/register`), login with JWT issuance (`/auth/login`), and password changes (`/auth/change-password`) |
| 2.0 | Data Ingestion & Cleaning | `pipeline/data_pipeline.py` → `DataPipeline.ingest()` | Handles CSV upload (`/upload`), manual entry (`/data-entries`), validation, cleaning, and deduplication |
| 3.0 | Feature Enrichment | `pipeline/feature_engineering.py` → `FeatureEngineeringService.enrich()` | Converts raw billing records into enriched records with 9 exogenous variables; computes seasonal fallbacks for future months |
| 4.0 | SARIMAX Model Training | `model/sarimax_model.py` → `SARIMAXModel.train()` | Trains SARIMAX model on enriched historical data (80/10/10 split, auto_arima); persists `.joblib` artefact |
| 5.0 | SARIMAX Forecasting | `model/sarimax_model.py` → `SARIMAXModel.forecast()` | Generates kWh predictions with 95% confidence intervals for 1/3/6/9/12-month horizons; derives price via `kWh × meralco_rate` |
| 6.0 | RAG Chat (Retrieval-Augmented Generation) | `rag/rag_service.py` → `RAGService.stream_answer()` | Answers natural-language questions by retrieving forecast/EDA context from ChromaDB, then streaming LLM response |
| 7.0 | Meralco Rate Scraper | `scraper/meralco_rate.py` → `get_rate()` / `refresh_rate()` | Downloads and parses Meralco rate schedule PDF; caches result in-memory (24h TTL) |
| 8.0 | Health Monitoring | `api/main.py` → `health()` | Probes all subsystems (SQLite, Ollama, model artefact, ChromaDB) and reports operational status |

### Data Stores

| ID | Store | Technology | System Path / Module | Contents |
|----|-------|------------|---------------------|----------|
| D1 | User Database | SQLite | `data/wattif.db` — `users` table | id, email, password_hash, created_at |
| D2 | Billing Records | SQLite | `data/wattif.db` — `monthly_bill_records` table | PK(user_id, year_month), kwh, price, 9 exogenous columns |
| D3 | Data Entry Log | SQLite | `data/wattif.db` — `data_entry_log` table | id, user_id, year_month, kwh, bill_amount, source, label |
| D4 | Chat History | SQLite | `data/wattif.db` — `chat_history` table | id, user_id, role, text, created_at |
| D5 | Model Artefacts | Filesystem (.joblib) | `data/models/{user_id}/sarimax_model.joblib` | Per-user trained SARIMAX model (order, MAPE, training window) |
| D6 | Forecast Vector Store | ChromaDB (persistent) | `data/chroma/` — collection `forecast_documents` | Forecast document embeddings (all-MiniLM-L6-v2), user-scoped |
| D7 | EDA Summaries Store | ChromaDB (persistent) | `storage/eda_store.py` | 17 EDA narrative summaries for RAG context |
| D8 | Rate Cache | In-memory (Python dict) | `scraper/meralco_rate.py` module-level | `MeralcoRateResult` with 24h TTL |
| D9 | Saved Forecasts | SQLite | `data/wattif.db` — `saved_forecasts` table | user_id (UNIQUE), horizon, months (JSON blob) |
| D10 | User Settings | SQLite | `data/wattif.db` — `user_settings` table | user_id, customer_type, horizons, thresholds |

### Level 1 Diagram

```
┌──────┐
│ User │
└──┬───┘
   │
   │ ① Credentials (email, password)
   ▼
┌──────────────────────────┐  Write: new user   ┌────────────────────┐
│ 1.0 User Authentication  │ ──────────────────► │ D1 User Database   │
│ (api/auth.py)            │ ◄────────────────── │ (users table)      │
└───────────┬──────────────┘  Read: stored creds └────────────────────┘
            │ ② JWT Token (HS256, 24h)
            ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │                   Authenticated Requests (Bearer JWT)              │
   └───────────────────────────────────────────────────────────────────┘
         │              │              │              │             │
         ▼              ▼              ▼              ▼             ▼
┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────┐ ┌─────────────┐
│ 2.0 Data     │ │ 5.0 SARIMAX│ │ 6.0 RAG    │ │ 7.0 Meralco │ │ 8.0 Health  │
│ Ingestion &  │ │ Forecasting│ │ Chat       │ │ Rate Scraper│ │ Monitoring  │
│ Cleaning     │ │            │ │            │ │             │ │             │
└──────┬───────┘ └──────┬─────┘ └──────┬─────┘ └──────┬──────┘ └─────────────┘
       │                │              │               │
       │ Write:         │              │               │
       │ cleaned rows   │              │               ▼
       ▼                │              │        ┌─────────────────────┐
┌────────────────┐      │              │        │ Meralco S3 Bucket   │
│ D2 Billing     │      │              │        └─────────────────────┘
│ Records        │      │              │               │
│ D3 Entry Log   │      │              │               │ Write: parsed rates
└──┬──────┬──────┘      │              │               ▼
   │      │             │              │        ┌────────────────┐
   │      │ Read:       │              │        │ D8 Rate Cache  │
   │      │ raw records │              │        │ (in-memory)    │
   │      ▼             │              │        └───┬────────────┘
   │ ┌──────────────────┐   Read: rate │            │
   │ │ 3.0 Feature      │◄────────────┼────────────┘
   │ │ Enrichment       │             │
   │ │ (FeatureEng.Svc) │             │
   │ └───────┬──────────┘             │
   │         │                        │
   │         │ Write: enriched        │
   │         │ records back           │
   │         ▼                        │
   │  ┌──────────────────┐           │   Read:        ┌────────────────────┐
   │  │ 4.0 SARIMAX      │           │   forecast     │ D6 Forecast Vector │
   │  │ Model Training   │           │   docs         │ Store (ChromaDB)   │
   │  └───────┬──────────┘           │                └──┬─────────────────┘
   │          │                       │                   │
   │          │ Write: .joblib        │                   │ Read: top-12 docs
   │          ▼                       │                   ▼
   │  ┌────────────────┐             │            ┌────────────┐
   │  │ D5 Model       │             │            │ 6.0 RAG    │
   │  │ Artefacts      │             │            │ Chat       │
   │  │ (.joblib)      │             │            └──────┬─────┘
   │  └───┬────────────┘             │                   │
   │      │                          │                   │ Read: top-3 EDA
   │      │ Read: load model         │                   ▼
   │      ▼                          │            ┌────────────────┐
   │   5.0 SARIMAX ──────────────────┘            │ D7 EDA Summary │
   │   Forecasting                                │ Store (ChromaDB)│
   │      │                                       └────────────────┘
   │      │ Write: forecast docs
   │      ▼                          Write: messages
   │   ┌────────────────────┐        ┌────────────────┐
   │   │ D6 Forecast Vector │        │ D4 Chat History│ ◄── 6.0 RAG Chat
   │   │ Store (ChromaDB)   │        └────────────────┘
   │   └────────────────────┘
   │
   │  Read: historical     Write: saved forecast
   │  records for 5.0      ┌──────────────┐
   └───────────────────────►│ D9 Saved     │ ◄── 5.0 Forecasting
                            │ Forecasts    │
                            └──────────────┘
                                               Read: thresholds
                            ┌──────────────┐ ──────────► 5.0 Forecasting
                            │ D10 User     │
                            │ Settings     │
                            └──────────────┘
```                                 └──────────────┘
```

### Level 1 Data Flows

| # | From | To | Data | API Endpoint / Function |
|---|------|----|------|------------------------|
| 1 | User | 1.0 User Authentication | Email, password | `POST /auth/register`, `POST /auth/login` |
| 2 | 1.0 User Authentication | User | JWT token (HS256, 24h expiry) | Response body |
| 3 | 1.0 User Authentication | D1 User Database | New user record (email, bcrypt hash, created_at) | `INSERT INTO users` |
| 4 | D1 User Database | 1.0 User Authentication | Stored credentials for verification | `SELECT … FROM users` |
| 5 | User | 2.0 Data Ingestion & Cleaning | CSV file (≤ 10 MB) or manual entry (year_month, kWh, bill_amount) | `POST /upload`, `POST /data-entries` |
| 6 | 2.0 Data Ingestion & Cleaning | D2 Billing Records | Cleaned/validated/deduplicated billing rows | `INSERT OR REPLACE INTO monthly_bill_records` |
| 7 | 2.0 Data Ingestion & Cleaning | D3 Data Entry Log | Audit trail entry (source: csv/manual) | `INSERT INTO data_entry_log` |
| 8 | D2 Billing Records | 3.0 Feature Enrichment | Raw billing records (kwh, year_month, existing exog values) | `SELECT … FROM monthly_bill_records` |
| 9 | 3.0 Feature Enrichment | 4.0 SARIMAX Model Training | `list[EnrichedRecord]` (9 exogenous columns populated) | Internal Python call |
| 10 | D2 Billing Records | 4.0 SARIMAX Model Training | Historical enriched records for train/val/test split | `DataPipeline.get_monthly_records()` |
| 11 | 4.0 SARIMAX Model Training | D5 Model Artefacts | Trained SARIMAX model (`.joblib` file) | `joblib.dump()` → `data/models/{user_id}/` |
| 12 | D5 Model Artefacts | 5.0 SARIMAX Forecasting | Loaded model for prediction | `SARIMAXModel.load()` → `joblib.load()` |
| 13 | 3.0 Feature Enrichment | 5.0 SARIMAX Forecasting | `list[ExogenousRow]` for future months (seasonal fallbacks) | `FeatureEngineeringService.enrich_forecast_horizon()` |
| 14 | D8 Rate Cache | 5.0 SARIMAX Forecasting | Current Meralco rate (₱/kWh) for price derivation | `get_rate().get_type("residential")` |
| 15 | 5.0 SARIMAX Forecasting | User | `ForecastResponse` (months: kWh, price, CI lower/upper, exog values) | `POST /forecast` response |
| 16 | 5.0 SARIMAX Forecasting | D6 Forecast Vector Store | `ForecastDocument` text + metadata per month | `VectorStore.upsert()` |
| 17 | 5.0 SARIMAX Forecasting | D9 Saved Forecasts | Persisted forecast JSON (user request) | `POST /saved-forecast` |
| 18 | User | 6.0 RAG Chat | Natural-language question string | `POST /ask` |
| 19 | D6 Forecast Vector Store | 6.0 RAG Chat | Top-12 relevant `ForecastDocument` objects (cosine similarity) | `VectorStore.query(top_k=12)` |
| 20 | D7 EDA Summary Store | 6.0 RAG Chat | Top-3 EDA narrative summaries (if question needs historical context) | `EDAStore.query(top_k=3)` |
| 21 | 6.0 RAG Chat | Ollama LLM | JSON messages array (system prompt + context + question) | `POST http://localhost:11434/api/chat` |
| 22 | Ollama LLM | 6.0 RAG Chat | Streamed answer tokens (chunked JSON, `<think>` blocks stripped) | Chunked HTTP response |
| 23 | 6.0 RAG Chat | User | SSE-streamed answer (token/done/error events) | `text/event-stream` response |
| 24 | 6.0 RAG Chat | D4 Chat History | Persisted user/assistant messages | `INSERT INTO chat_history` |
| 25 | 7.0 Meralco Rate Scraper | Meralco S3 Bucket | HTTP GET for rate PDF | `httpx.Client.get(url)` |
| 26 | Meralco S3 Bucket | 7.0 Meralco Rate Scraper | PDF file (Summary Schedule of Rates) | Binary response content |
| 27 | 7.0 Meralco Rate Scraper | D8 Rate Cache | `MeralcoRateResult` (customer types + brackets, 24h TTL) | Module-level cache variable |
| 28 | 7.0 Meralco Rate Scraper | User | Rate breakdown by customer type | `GET /meralco-rate` response |
| 29 | 2.0 Data Ingestion & Cleaning | 4.0 SARIMAX Model Training | Auto-retrain trigger (background thread) | `_run_retraining_background()` |
| 30 | D10 User Settings | 5.0 SARIMAX Forecasting | kWh/bill thresholds for warning generation | `SELECT … FROM user_settings` |
| 31 | D4 Chat History | 6.0 RAG Chat | Previous conversation messages (for context, if needed) | `SELECT … FROM chat_history` |
| 32 | D2 Billing Records | 5.0 SARIMAX Forecasting | Historical records for exogenous estimation | `SELECT … FROM monthly_bill_records` |
| 33 | User | 8.0 Health Monitoring | Health check request | `GET /health` |
| 34 | 8.0 Health Monitoring | User | Subsystem status (db, ollama, model, chromadb) | JSON response |

### Data Store Input/Output (Read/Write) Summary

The following table explicitly documents every inflow (write) and outflow (read) for each data store, satisfying the DFD rule that all data stores must show both their sources and consumers.

| Data Store | Inflows (Write) | Outflows (Read) |
|------------|-----------------|-----------------|
| **D1 User Database** (`users`) | ← 1.0 User Authentication: new user record (email, bcrypt hash) | → 1.0 User Authentication: stored credentials for login verification |
| **D2 Billing Records** (`monthly_bill_records`) | ← 2.0 Data Ingestion: cleaned/deduplicated billing rows | → 3.0 Feature Enrichment: raw records for enrichment |
| | ← 2.0 Data Ingestion: bridged manual entry rows | → 4.0 Model Training: enriched historical records for train/val/test |
| | | → 5.0 Forecasting: historical records for exogenous estimation |
| **D3 Data Entry Log** (`data_entry_log`) | ← 2.0 Data Ingestion: audit entry (CSV or manual source) | → User (via `GET /data-entries`): list of all entries with exog values |
| **D4 Chat History** (`chat_history`) | ← 6.0 RAG Chat: persisted user question + assistant answer | → User (via `GET /chat-history`): 100 most recent messages |
| | | → 6.0 RAG Chat: previous messages for continuity |
| **D5 Model Artefacts** (`.joblib` files) | ← 4.0 Model Training: serialized SARIMAX model (`joblib.dump`) | → 5.0 Forecasting: loaded model object (`joblib.load`) |
| | | → 8.0 Health Monitoring: existence check for health probe |
| **D6 Forecast Vector Store** (ChromaDB) | ← 5.0 Forecasting: embedded `ForecastDocument` per forecast month | → 6.0 RAG Chat: top-12 similar documents (cosine similarity, user-scoped) |
| | | → 8.0 Health Monitoring: collection count check |
| **D7 EDA Summary Store** (ChromaDB) | ← EDA ingestion script (`data/ingest_eda.py`): 17 narrative summaries | → 6.0 RAG Chat: top-3 EDA docs (when question needs historical context) |
| **D8 Rate Cache** (in-memory) | ← 7.0 Meralco Rate Scraper: `MeralcoRateResult` (24h TTL) | → 5.0 Forecasting: current ₱/kWh rate for price derivation |
| | | → 3.0 Feature Enrichment: rate value for exogenous column |
| | | → User (via `GET /meralco-rate`): full rate breakdown |
| **D9 Saved Forecasts** (`saved_forecasts`) | ← 5.0 Forecasting (via `POST /saved-forecast`): forecast JSON blob | → User (via `GET /saved-forecast`): most recent saved forecast |
| **D10 User Settings** (`user_settings`) | ← User (via `PUT /settings`): customer_type, thresholds, horizons | → 5.0 Forecasting: threshold values for warning generation |
| | | → User (via `GET /settings`): current settings |

---

## 4. Level 2 DFD — Process 2.0: Data Ingestion & Cleaning

This decomposition shows how `DataPipeline.ingest()` and the `/data-entries` endpoints process incoming data.

```
┌──────┐                                              ┌────────────────────┐
│ User │                                              │ D2 Billing Records │
└──┬───┘                                              │ D3 Data Entry Log  │
   │                                                  └────────┬───────────┘
   │ CSV File (POST /upload)                                   │
   ├──────────────────┐                                        │
   │                  ▼                                        │
   │         ┌──────────────────────┐                          │
   │         │ 2.1 Validate &       │                          │
   │         │ Parse CSV            │                          │
   │         │ (DataPipeline.ingest)│                          │
   │         └──────────┬───────────┘                          │
   │                    │ Parsed rows (year_month, kWh, price) │
   │                    ▼                                      │
   │         ┌──────────────────────┐                          │
   │         │ 2.2 Clean & Impute   │                          │
   │         │ (handle NaN, gaps,   │                          │
   │         │  invalid dates)      │                          │
   │         └──────────┬───────────┘                          │
   │                    │ Cleaned rows                         │
   │                    ▼                                      │
   │         ┌──────────────────────┐   Deduplicated rows      │
   │         │ 2.3 Deduplicate      │ ────────────────────────►│
   │         │ & Store (UPSERT by   │   Entry log records      │
   │         │  user_id+year_month) │ ────────────────────────►│
   │         └──────────┬───────────┘                          │
   │                    │ Cleaning report (rows_added,         │
   │◄───────────────────┘   rows_skipped, duplicates_merged)   │
   │                                                           │
   │ Manual Entry (POST /data-entries)                         │
   ├──────────────────┐                                        │
   │                  ▼                                        │
   │         ┌──────────────────────┐   Entry row              │
   │         │ 2.4 Validate &       │ ────────────────────────►│
   │         │ Bridge Manual Entry  │                          │
   │         │ (_bridge_entry_to_   │   Billing record         │
   │         │  bill_records)       │ ────────────────────────►│
   │         └──────────┬───────────┘                          │
   │                    │                                      │
   │                    ▼                                      │
   │         ┌──────────────────────┐                          │
   │         │ 2.5 Check Auto-      │    Trigger               │
   │         │ Retrain Threshold    │ ──────────► [4.0 SARIMAX │
   │         │ (_run_retraining_    │              Training]    │
   │         │  background)         │                          │
   │         └──────────────────────┘                          │
   │                                                           │
   │◄──── UploadResponse / DataEntryRow (confirmation)         │
   │                                                           │
```

### Process 2.0 Sub-processes

| # | Process | Input | Output | Module Reference |
|---|---------|-------|--------|-----------------|
| 2.1 | Validate & Parse CSV | Raw CSV file (≤ 10 MB, columns: year_month, kwh, price) | Parsed rows with validated types | `DataPipeline.ingest()` |
| 2.2 | Clean & Impute Data | Parsed rows | Cleaned rows (invalid dates removed, NaN handled) | `DataPipeline.ingest()` internal logic |
| 2.3 | Deduplicate & Store | Cleaned rows | Deduplicated records → D2; Entry log → D3; Cleaning report → User | `INSERT OR REPLACE INTO monthly_bill_records` |
| 2.4 | Validate & Bridge Manual Entry | year_month, kWh, bill_amount | Validated entry → D3 + bridged billing record → D2 | `_bridge_entry_to_bill_records()` |
| 2.5 | Check Auto-Retrain | Record count + user model state | Background retraining trigger (if new data warrants it) | `_run_retraining_background()` |

---

## 5. Level 2 DFD — Process 5.0: SARIMAX Forecasting

This decomposition shows how `POST /forecast` generates predictions via `SARIMAXModel.forecast()`.

```
┌──────┐                                                  ┌──────────────────┐
│ User │                                                  │ D5 Model         │
└──┬───┘                                                  │ Artefacts        │
   │                                                      └────────┬─────────┘
   │ ForecastRequest {horizon: 1|3|6|9|12}                         │
   │ (POST /forecast)                                              │
   ▼                                                               │
┌───────────────────────────┐   Load .joblib                       │
│ 5.1 Load User Model       │◄────────────────────────────────────┘
│ (SARIMAXModel.load)       │
└────────────┬──────────────┘
             │ Loaded SARIMAX model object
             ▼
┌───────────────────────────┐  Historical records   ┌──────────────────┐
│ 5.2 Compute Future        │◄─────────────────────│ D2 Billing       │
│ Exogenous Variables       │                       │ Records          │
│ (FeatureEngineeringService│                       └──────────────────┘
│  .enrich_forecast_horizon)│
└────────────┬──────────────┘
             │ ExogenousRow[] (9 vars × horizon months)
             ▼
┌───────────────────────────┐
│ 5.3 Generate kWh Forecast │
│ (SARIMAX.get_forecast +   │
│  conf_int at α=0.05)      │
└────────────┬──────────────┘
             │ kWh predictions + 95% CI (lower, upper)
             ▼
┌───────────────────────────┐                       ┌──────────────────┐
│ 5.4 Derive Price           │◄────────────────────│ D8 Rate Cache    │
│ (predicted_kWh ×           │   Meralco rate/kWh  └──────────────────┘
│  meralco_rate)             │
└────────────┬──────────────┘
             │ ForecastMonth[] (kWh, price, CI, exog values)
             ├─────────────────────────────────┐
             │                                 ▼
             │                       ┌──────────────────────┐
             │                       │ 5.5 Embed & Store    │
             │                       │ in Vector Store      │
             │                       │ (VectorStore.upsert) │
             │                       └──────────┬───────────┘
             │                                  │
             │                                  ▼
             │                       ┌──────────────────────┐
             │                       │ D6 Forecast Vector   │
             │                       │ Store (ChromaDB)     │
             │                       └──────────────────────┘
             ▼
┌───────────────────────────┐                       ┌──────────────────┐
│ 5.6 Check Thresholds &    │◄─────────────────────│ D10 User Settings│
│ Generate Warnings         │   kwh_threshold,      └──────────────────┘
│                           │   bill_threshold
└────────────┬──────────────┘
             │ ForecastResponse + warnings[]
             ▼
          ┌──────┐
          │ User │
          └──────┘
```

---

## 6. Level 2 DFD — Process 6.0: RAG Chat

This decomposition shows how `POST /ask` answers questions via `RAGService.stream_answer()`.

```
┌──────┐                                                ┌──────────────────┐
│ User │                                                │ Ollama LLM       │
└──┬───┘                                                │ (qwen3:1.7b)     │
   │                                                    └────────┬─────────┘
   │ AskRequest {question: string}                               │
   │ (POST /ask)                                                 │
   ▼                                                             │
┌───────────────────────────┐                                    │
│ 6.1 Scope Check           │── Out of scope ──► "I can only     │
│ (RAGService._is_in_scope) │                    answer questions │
│                           │                    about electricity│
│                           │                    bills" ──► User  │
└────────────┬──────────────┘                                    │
             │ In-scope question                                 │
             ▼                                                   │
┌───────────────────────────┐  Top-12 docs    ┌─────────────────────┐
│ 6.2 Retrieve Forecast     │◄───────────────│ D6 Forecast Vector  │
│ Context                   │                 │ Store (ChromaDB)    │
│ (VectorStore.query        │                 └─────────────────────┘
│  top_k=12, user-scoped)   │
└────────────┬──────────────┘
             │
             │ (If _needs_eda(question) == True)
             │                                    ┌─────────────────────┐
             │◄──── Top-3 EDA summaries ─────────│ D7 EDA Summary      │
             │      (EDAStore.query, top_k=3)    │ Store (ChromaDB)    │
             │                                    └─────────────────────┘
             ▼
┌───────────────────────────┐
│ 6.3 Build Prompt          │
│ (RAGService._build_       │
│  messages)                │
│  • System prompt          │
│  • Forecast context       │
│  • EDA context (optional) │
│  • User question          │
└────────────┬──────────────┘
             │ Messages array (JSON)
             ▼
┌───────────────────────────┐  POST /api/chat (stream=true)      │
│ 6.4 Stream LLM Response   │──────────────────────────────────►│
│ (httpx streaming +         │◄──────────────────────────────────│
│  _strip_think_blocks)     │  Chunked token stream              │
└────────────┬──────────────┘
             │
             │ SSE events: {type: "token"|"done"|"error", data: ...}
             ├───────────────────────────────┐
             ▼                               ▼
          ┌──────┐                  ┌────────────────────┐
          │ User │                  │ D4 Chat History    │
          └──────┘                  │ (chat_history tbl) │
                                    └────────────────────┘
```

---

## 7. Level 2 DFD — Process 7.0: Meralco Rate Scraper

This decomposition shows how `scraper/meralco_rate.py` obtains and caches rate data.

```
┌──────┐                                           ┌─────────────────────┐
│ User │                                           │ Meralco S3 Bucket   │
└──┬───┘                                           └──────────┬──────────┘
   │                                                          │
   │ GET /meralco-rate                                        │
   │ (or POST /meralco-rate/refresh)                          │
   ▼                                                          │
┌───────────────────────────┐                                 │
│ 7.1 Check Cache TTL       │                                 │
│ (module-level _cache var) │                                 │
└────────────┬──────────────┘                                 │
             │                                                │
             │ Cache miss (>24h or refresh forced)            │
             ▼                                                │
┌───────────────────────────┐   HTTP GET PDF                  │
│ 7.2 Download Rate PDF     │────────────────────────────────►│
│ (_fetch_and_parse)        │◄────────────────────────────────│
│ • Try current month       │   PDF binary content            │
│ • Try prior 2 months      │                                 │
└────────────┬──────────────┘                                 │
             │ PDF bytes
             ▼
┌───────────────────────────┐
│ 7.3 Parse PDF Tables      │
│ (pdfplumber.open →        │
│  extract_table →          │
│  _row_to_bracket)         │
└────────────┬──────────────┘
             │ list[CustomerType] (Residential, GSA, GSB)
             │   each with list[RateBracket]
             ▼
┌───────────────────────────┐        ┌──────────────────┐
│ 7.4 Build & Cache Result  │ ──────►│ D8 Rate Cache    │
│ (MeralcoRateResult with   │        │ (in-memory, 24h) │
│  fetched_at + is_fallback)│        └──────────────────┘
└────────────┬──────────────┘
             │
             │ (If all downloads fail)
             ▼
┌───────────────────────────┐
│ 7.5 Fallback Rates        │
│ (_fallback: hardcoded     │
│  June 2026 rates)         │
└────────────┬──────────────┘
             │ MeralcoRateResult (is_fallback=True)
             ▼
          ┌──────┐
          │ User │  ← MeralcoRateResponse (customer_types, brackets)
          └──────┘
```

---

## 8. Data Dictionary

### External Data Flows

| Data Flow | Description | Format | Endpoint |
|-----------|-------------|--------|----------|
| Credentials | Email + password for registration/login | JSON: `{email, password}` | `POST /auth/register`, `POST /auth/login` |
| JWT Token | Authentication bearer token | String (HS256-signed, 24h expiry, claims: sub, email, iat, exp) | Response body |
| CSV File | Monthly electricity bill history | CSV (columns: year_month, kwh, price + optional 9 exog columns) | `POST /upload` |
| Manual Entry | Single billing month data point | JSON: `{year_month, kwh, bill_amount}` | `POST /data-entries` |
| Forecast Request | Desired prediction horizon | JSON: `{horizon: 1\|3\|6\|9\|12}` | `POST /forecast` |
| Forecast Response | Predicted kWh/price per month with CI | JSON: `{months: ForecastMonth[], horizon}` | Response body |
| Chat Question | Natural-language query about bills | JSON: `{question: string}` | `POST /ask` |
| Chat Answer | LLM-generated response | SSE stream: `{type: "token"\|"done"\|"error", data: ...}` events | `text/event-stream` |
| Rate PDF | Meralco Summary Schedule of Rates | PDF (parsed via `pdfplumber`) | Downloaded from S3 |
| Rate Response | Parsed rate brackets per customer type | JSON: `{customer_types: [...], effective_month, is_fallback}` | `GET /meralco-rate` |

### Internal Data Stores Schema

| Store | Table / Path | Key Fields | Purpose |
|-------|-------------|-----------|---------|
| `monthly_bill_records` | SQLite table | PK(user_id, year_month), kwh, price, 9 exog columns, session_id, created_at | Primary training/forecast data |
| `data_entry_log` | SQLite table | id, user_id, year_month, kwh, bill_amount, source, label, created_at | Audit trail of all data entries |
| `users` | SQLite table | id, email, password_hash, created_at | Account management |
| `user_settings` | SQLite table | user_id (UNIQUE), customer_type, horizons, thresholds | Per-user preferences |
| `chat_history` | SQLite table | id, user_id, role, text, created_at | Conversation persistence |
| `saved_forecasts` | SQLite table | user_id (UNIQUE), horizon, months (JSON blob) | Last forecast cache |
| `training_log` | SQLite table | id, user_id, trained_at, mape, window | Model retraining history |
| ChromaDB `forecast_documents` | `data/chroma/` | ID: `{user_id}_{month}_{horizon}`, embeddings (all-MiniLM-L6-v2) | Semantic search for RAG |
| EDA Summaries | ChromaDB collection | 17 summary documents (eda_overview, eda_annual_*, etc.) | Historical analysis context |
| SARIMAX `.joblib` | `data/models/{user_id}/sarimax_model.joblib` | model object, order, MAPE, training window, exog columns | Trained forecasting model |
| Rate Cache | In-memory Python variable | `MeralcoRateResult` (customer_types, fetched_at, is_fallback) | Avoid repeated PDF downloads |

### Exogenous Variables (9 columns in `monthly_bill_records`)

| Variable | Column Name | Source | Description |
|----------|-------------|--------|-------------|
| Meralco Rate | `meralco_rate` | CSV data / `scraper/meralco_rate.py` | ₱/kWh residential electricity rate |
| Average Temperature | `avg_temperature` | CSV data / PAGASA priors for forecast | Monthly average temperature (°C) |
| Average Humidity | `avg_humidity` | CSV data / PAGASA priors for forecast | Monthly average relative humidity (%) |
| Total Rainfall | `total_rainfall_mm` | CSV data / PAGASA priors for forecast | Total monthly rainfall (mm) |
| Holiday Count | `holiday_count` | CSV data / calendar computation | Number of public holidays in the month |
| Weekend Count | `weekend_count` | CSV data / `calendar.monthrange()` | Number of Saturday/Sunday days |
| Hot Days Count | `hot_days_count` | CSV data / PAGASA priors for forecast | Days with temperature > threshold |
| Rainy Days Count | `rainy_days_count` | CSV data / PAGASA priors for forecast | Days with measurable rainfall |
| El Niño Phase | `is_el_nino` | CSV data / historical mean for forecast | Binary indicator (1 = El Niño active) |

---

## 9. Balancing Summary

The following table verifies that each Level 1 process has consistent inputs/outputs between levels (DFD balancing rule).

| Process | Inputs at Level 1 | Outputs at Level 1 | Decomposed at Level 2? |
|---------|-------------------|--------------------|-----------------------|
| 1.0 User Authentication | User credentials, D1 stored creds | JWT token, D1 new user record | No (simple CRUD) |
| 2.0 Data Ingestion & Cleaning | CSV file, manual entry | D2 billing records, D3 entry log, cleaning report, retrain trigger | Yes (§4) |
| 3.0 Feature Enrichment | D2 raw records, D8 rate cache | Enriched records → 4.0, ExogenousRow[] → 5.0 | No (pass-through service) |
| 4.0 SARIMAX Model Training | Enriched records | D5 model artefact (.joblib) | No (single auto_arima call) |
| 5.0 SARIMAX Forecasting | D5 model, exog rows, D8 rate, D10 settings | User forecast, D6 vector docs, D9 saved forecast | Yes (§5) |
| 6.0 RAG Chat | User question, D6 forecast docs, D7 EDA docs | SSE answer → User, D4 chat history | Yes (§6) |
| 7.0 Meralco Rate Scraper | Meralco S3 PDF | D8 rate cache, rate response → User | Yes (§7) |
| 8.0 Health Monitoring | All subsystem probes | Health status → User | No (single aggregation) |

---

## 10. Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | July 2026 | Development Team | Initial document creation |
| 2.0 | July 2026 | Development Team | Major revision: added SARIMAX Forecasting to Level 0 context; renamed "Meralco S3" to "Meralco Rate Scraper" process; updated all process names to reference actual system modules; added Level 2 DFD for Meralco Rate Scraper (§7); removed phantom Open-Meteo/NOAA external entities (data is pre-populated in CSV); added EDA Store (D7), Data Entry Log (D3), User Settings (D10); added Data Store Input/Output Summary with explicit read/write flows per store; added balancing summary (§9); added API endpoint references to all data flows; updated Level 1 diagram with labeled bidirectional data store arrows |
