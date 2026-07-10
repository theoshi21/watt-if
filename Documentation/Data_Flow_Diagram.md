# Data Flow Diagram (DFD) — WATT-IF

**Document Version:** 1.0  
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
| **Meralco S3** | Meralco's AWS S3 bucket hosting PDF rate schedule documents |
| **Open-Meteo API** | Weather API providing temperature, humidity, and rainfall data |
| **NOAA ONI** | National Oceanic and Atmospheric Administration providing El Niño/ENSO phase data |
| **Ollama LLM** | Local language model service (qwen3:1.7b) for generating natural-language answers |

### Level 0 Diagram

```
                                ┌─────────────┐
                                │ Meralco S3  │
                                └──────┬──────┘
                                       │ Rate PDF
                                       ▼
┌──────┐   Credentials/Data    ┌──────────────────┐   Weather Query    ┌──────────────┐
│      │ ──────────────────► │                  │ ─────────────────► │ Open-Meteo   │
│      │                      │                  │ ◄───────────────── │ API          │
│      │   Forecasts/          │                  │   Weather Data     └──────────────┘
│ User │   Answers/            │    WATT-IF       │
│      │   Reports             │    System        │   ENSO Query       ┌──────────────┐
│      │ ◄──────────────────  │                  │ ─────────────────► │ NOAA ONI     │
│      │                      │                  │ ◄───────────────── │              │
└──────┘                      │                  │   ENSO Phase       └──────────────┘
                                │                  │
                                │                  │   Question/Context ┌──────────────┐
                                │                  │ ─────────────────► │ Ollama LLM   │
                                │                  │ ◄───────────────── │              │
                                └──────────────────┘   Answer Tokens   └──────────────┘
```

### Level 0 Data Flows

| # | From | To | Data |
|---|------|----|------|
| 1 | User | WATT-IF System | Registration credentials, login credentials, CSV files, manual data entries, forecast requests, chat questions, settings |
| 2 | WATT-IF System | User | JWT token, forecast results (kWh, price, CI), chat answers (streamed), data entries, health status, Meralco rates |
| 3 | Meralco S3 | WATT-IF System | PDF rate schedule document |
| 4 | Open-Meteo API | WATT-IF System | Temperature, humidity, rainfall data per month |
| 5 | NOAA ONI | WATT-IF System | El Niño/La Niña phase indicator |
| 6 | WATT-IF System | Ollama LLM | System prompt + forecast context + user question |
| 7 | Ollama LLM | WATT-IF System | Streamed answer tokens |

---

## 3. Level 1 DFD

The Level 1 DFD decomposes the WATT-IF system into its major processes.

### Processes

| # | Process | Description |
|---|---------|-------------|
| 1.0 | Authentication | Manages user registration, login (JWT issuance), and password changes |
| 2.0 | Data Ingestion | Handles CSV upload, manual entry, and data cleaning/validation |
| 3.0 | Feature Enrichment | Resolves exogenous variables (weather, rate, ENSO) for each billing record |
| 4.0 | Model Training | Trains the SARIMAX forecasting model on enriched historical data |
| 5.0 | Forecasting | Generates kWh/price forecasts with 95% confidence intervals |
| 6.0 | RAG Chat | Answers natural-language questions using retrieved forecast context + LLM |
| 7.0 | Rate Scraping | Downloads and parses Meralco rate schedules from PDF |
| 8.0 | Health Monitoring | Probes all subsystems and reports operational status |

### Data Stores

| ID | Store | Technology | Contents |
|----|-------|------------|----------|
| D1 | User Database | SQLite | users, user_settings |
| D2 | Billing Records | SQLite | monthly_bill_records, data_entry_log |
| D3 | Chat History | SQLite | chat_history |
| D4 | Model Artefacts | Filesystem (.joblib) | Per-user SARIMAX models (data/models/{user_id}/) |
| D5 | Vector Store | ChromaDB | Forecast document embeddings (per-user collections) |
| D6 | Rate Cache | In-memory | Meralco rate result (24h TTL) |
| D7 | Saved Forecasts | SQLite | saved_forecasts |

### Level 1 Diagram

```
┌──────┐
│ User │
└──┬───┘
   │
   │ ① Credentials
   ▼
┌─────────────────┐        ┌────────────────┐
│ 1.0             │ ◄────► │ D1 User DB     │
│ Authentication  │        └────────────────┘
└────────┬────────┘
         │ ② JWT Token
         ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                   Authenticated Requests                     │
   └─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────┐
│ 2.0         │  │ 5.0       │  │ 6.0       │  │ 7.0           │
│ Data        │  │ Forecast  │  │ RAG Chat  │  │ Rate Scraping │
│ Ingestion   │  │           │  │           │  │               │
└──────┬──────┘  └─────┬─────┘  └─────┬─────┘  └───────┬───────┘
       │                │              │                │
       ▼                │              │                ▼
┌────────────────┐      │              │         ┌──────────────┐
│ D2 Billing     │      │              │         │ Meralco S3   │
│ Records        │      │              │         └──────────────┘
└───────┬────────┘      │              │                │
        │               │              │                ▼
        ▼               │              │         ┌────────────────┐
┌─────────────┐         │              │         │ D6 Rate Cache  │
│ 3.0 Feature │         │              │         └────────────────┘
│ Enrichment  │◄────────┼──────────────┼─────────────────┘
└──────┬──────┘         │              │
       │                │              │
       ▼                │              ▼
┌─────────────┐         │       ┌────────────────┐
│ 4.0 Model   │         │       │ D5 Vector      │
│ Training    │         │       │ Store          │
└──────┬──────┘         │       └───────┬────────┘
       │                │               │
       ▼                ▼               ▼
┌────────────────┐  ┌────────────────┐  ┌──────────────┐
│ D4 Model       │  │ D7 Saved       │  │ Ollama LLM   │
│ Artefacts      │  │ Forecasts      │  └──────────────┘
└────────────────┘  └────────────────┘
```

### Level 1 Data Flows

| # | From | To | Data |
|---|------|----|------|
| 1 | User | 1.0 Authentication | Email, password |
| 2 | 1.0 Authentication | User | JWT token |
| 3 | 1.0 Authentication | D1 User DB | New user record (email, bcrypt hash) |
| 4 | D1 User DB | 1.0 Authentication | Stored credentials for verification |
| 5 | User | 2.0 Data Ingestion | CSV file or manual entry (year_month, kWh, bill) |
| 6 | 2.0 Data Ingestion | D2 Billing Records | Cleaned/validated billing rows |
| 7 | D2 Billing Records | 3.0 Feature Enrichment | Raw billing records (kWh, year_month) |
| 8 | Open-Meteo API | 3.0 Feature Enrichment | Temperature, humidity, rainfall |
| 9 | NOAA ONI | 3.0 Feature Enrichment | ENSO phase indicator |
| 10 | D6 Rate Cache | 3.0 Feature Enrichment | Current Meralco rate per kWh |
| 11 | 3.0 Feature Enrichment | D2 Billing Records | Enriched records (9 exogenous variables added) |
| 12 | D2 Billing Records | 4.0 Model Training | Enriched historical records |
| 13 | 4.0 Model Training | D4 Model Artefacts | Trained SARIMAX model (.joblib) |
| 14 | D4 Model Artefacts | 5.0 Forecasting | Loaded model for prediction |
| 15 | 5.0 Forecasting | User | Forecast months (kWh, price, 95% CI, exog values) |
| 16 | 5.0 Forecasting | D5 Vector Store | Forecast documents for RAG retrieval |
| 17 | 5.0 Forecasting | D7 Saved Forecasts | Persisted forecast (user request) |
| 18 | User | 6.0 RAG Chat | Natural-language question |
| 19 | D5 Vector Store | 6.0 RAG Chat | Top-K relevant forecast documents |
| 20 | 6.0 RAG Chat | Ollama LLM | Prompt (system + context + question) |
| 21 | Ollama LLM | 6.0 RAG Chat | Streamed answer tokens |
| 22 | 6.0 RAG Chat | User | SSE-streamed answer + source metadata |
| 23 | 6.0 RAG Chat | D3 Chat History | Persisted user/assistant messages |
| 24 | 7.0 Rate Scraping | Meralco S3 | HTTP request for rate PDF |
| 25 | Meralco S3 | 7.0 Rate Scraping | PDF file (rate schedule) |
| 26 | 7.0 Rate Scraping | D6 Rate Cache | Parsed rate brackets (cached 24h) |
| 27 | 7.0 Rate Scraping | User | Rate breakdown by customer type |

---

## 4. Level 2 DFD — Process 2.0: Data Ingestion

```
┌──────┐                                              ┌────────────────┐
│ User │                                              │ D2 Billing     │
└──┬───┘                                              │ Records        │
   │                                                  └───────┬────────┘
   │ CSV File                                                 │
   ├──────────────────┐                                       │
   │                  ▼                                       │
   │         ┌────────────────┐                               │
   │         │ 2.1 Validate   │                               │
   │         │ & Parse CSV    │                               │
   │         └───────┬────────┘                               │
   │                 │ Parsed rows                             │
   │                 ▼                                        │
   │         ┌────────────────┐                               │
   │         │ 2.2 Clean &    │                               │
   │         │ Impute Data    │                               │
   │         └───────┬────────┘                               │
   │                 │ Cleaned rows                            │
   │                 ▼                                        │
   │         ┌────────────────┐    Deduplicated rows          │
   │         │ 2.3 Deduplicate│ ─────────────────────────────►│
   │         │ & Store        │                               │
   │         └───────┬────────┘                               │
   │                 │ Cleaning report                         │
   │◄────────────────┘                                        │
   │                                                          │
   │ Manual Entry (year_month, kWh, bill)                     │
   ├──────────────────┐                                       │
   │                  ▼                                       │
   │         ┌────────────────┐    Entry row                  │
   │         │ 2.4 Validate   │ ─────────────────────────────►│
   │         │ Manual Entry   │                               │
   │         └───────┬────────┘                               │
   │                 │                                        │
   │                 ▼                                        │
   │         ┌────────────────┐    Trigger                    │
   │         │ 2.5 Check Auto │ ──────────────► [4.0 Training]│
   │         │ Retrain        │                               │
   │         └────────────────┘                               │
   │                                                          │
   │◄──────── Confirmation + retraining_triggered             │
   │                                                          │
```

### Process 2.0 Sub-processes

| # | Process | Input | Output |
|---|---------|-------|--------|
| 2.1 | Validate & Parse CSV | Raw CSV file (≤ 10 MB) | Parsed rows with year_month, kWh, price |
| 2.2 | Clean & Impute Data | Parsed rows | Cleaned rows (invalid dates removed, gaps imputed) |
| 2.3 | Deduplicate & Store | Cleaned rows | Deduplicated records → D2; Cleaning report → User |
| 2.4 | Validate Manual Entry | year_month, kWh, bill_amount | Validated entry row → D2 |
| 2.5 | Check Auto-Retrain | User settings + record count | Trigger model retraining if threshold met |

---

## 5. Level 2 DFD — Process 5.0: Forecasting

```
┌──────┐                                                 ┌────────────────┐
│ User │                                                 │ D4 Model       │
└──┬───┘                                                 │ Artefacts      │
   │                                                     └───────┬────────┘
   │ Forecast Request (horizon: 1/3/6/9/12)                      │
   │                                                             │
   ▼                                                             │
┌────────────────┐   Load model                                  │
│ 5.1 Load       │◄─────────────────────────────────────────────┘
│ User Model     │
└───────┬────────┘
        │ Loaded SARIMAX model
        ▼
┌────────────────┐   Historical records     ┌────────────────┐
│ 5.2 Estimate   │◄────────────────────────│ D2 Billing     │
│ Exogenous Vars │                          │ Records        │
└───────┬────────┘                          └────────────────┘
        │ Exogenous array (9 vars × horizon months)
        ▼
┌────────────────┐
│ 5.3 Generate   │
│ Forecast       │
│ (SARIMAX.predict)
└───────┬────────┘
        │ kWh predictions + 95% CI
        ▼
┌────────────────┐
│ 5.4 Derive     │
│ Price          │
│ (kWh × rate)  │
└───────┬────────┘
        │ ForecastMonth[]
        ├──────────────────────────────────────┐
        │                                      ▼
        │                            ┌────────────────┐
        │                            │ D5 Vector      │
        │                            │ Store (ChromaDB)│
        │                            └────────────────┘
        ▼
┌────────────────┐
│ 5.5 Check      │   User settings     ┌────────────────┐
│ Thresholds &   │◄───────────────────│ D1 User DB     │
│ Generate Warns │                     └────────────────┘
└───────┬────────┘
        │ Forecast + warnings
        ▼
     ┌──────┐
     │ User │
     └──────┘
```

---

## 6. Level 2 DFD — Process 6.0: RAG Chat

```
┌──────┐                                              ┌──────────────┐
│ User │                                              │ Ollama LLM   │
└──┬───┘                                              └──────┬───────┘
   │                                                         │
   │ Question                                                │
   ▼                                                         │
┌────────────────┐                                           │
│ 6.1 Scope      │── Out of scope ──► "Cannot answer" ──► User
│ Check          │                                           │
└───────┬────────┘                                           │
        │ In-scope question                                  │
        ▼                                                    │
┌────────────────┐   Top-12 docs     ┌────────────────┐     │
│ 6.2 Retrieve   │◄────────────────│ D5 Vector      │     │
│ Context        │                   │ Store          │     │
└───────┬────────┘                   └────────────────┘     │
        │                                                    │
        │ (If explanation-oriented question)                  │
        │         EDA docs           ┌────────────────┐     │
        │◄──────────────────────────│ EDA Store      │     │
        │                            └────────────────┘     │
        ▼                                                    │
┌────────────────┐                                           │
│ 6.3 Build      │                                           │
│ Prompt         │                                           │
│ (System +      │                                           │
│  Context +     │                                           │
│  Question)     │                                           │
└───────┬────────┘                                           │
        │ Messages array                                     │
        ▼                                                    │
┌────────────────┐   Prompt payload                          │
│ 6.4 Stream     │──────────────────────────────────────────►│
│ LLM Response   │◄──────────────────────────────────────────│
└───────┬────────┘   Token stream                            │
        │                                                    │
        │ SSE events (token/done/error)                      │
        ├───────────────────────────────┐                    │
        ▼                               ▼                    │
     ┌──────┐                  ┌────────────────┐            │
     │ User │                  │ D3 Chat        │            │
     └──────┘                  │ History        │            │
                               └────────────────┘            │
```

---

## 7. Data Dictionary

### External Data Flows

| Data Flow | Description | Format |
|-----------|-------------|--------|
| Credentials | Email + password for registration/login | JSON: `{email, password}` |
| JWT Token | Authentication bearer token | String (HS256-signed, 24h expiry) |
| CSV File | Monthly electricity bill history | CSV (year_month, kwh, price columns) |
| Manual Entry | Single billing month data point | JSON: `{year_month, kwh, bill_amount}` |
| Forecast Request | Desired prediction horizon | JSON: `{horizon: 1|3|6|9|12}` |
| Forecast Response | Predicted kWh/price per month | JSON array of ForecastMonth objects |
| Chat Question | Natural-language query about bills | JSON: `{question: string}` |
| Chat Answer | LLM-generated response | SSE stream: token/done/error events |
| Rate PDF | Meralco Schedule of Rates | PDF document (parsed via pdfplumber) |
| Weather Data | Monthly climate statistics | JSON (temperature, humidity, rainfall) |
| ENSO Phase | El Niño status indicator | Integer: -1 (La Niña) / 0 (Neutral) / 1 (El Niño) |

### Internal Data Stores

| Store | Key Fields | Purpose |
|-------|-----------|---------|
| monthly_bill_records | user_id, year_month, kwh, price, 9 exog columns | Primary training/forecast data |
| data_entry_log | id, user_id, year_month, kwh, bill_amount, source | Audit trail of all data entries |
| users | id, email, password_hash | Account management |
| user_settings | user_id, customer_type, horizons, thresholds | Per-user preferences |
| chat_history | id, user_id, role, text | Conversation persistence |
| saved_forecasts | user_id, horizon, months (JSON) | Last forecast cache |
| ChromaDB collections | document text, metadata, embeddings | Semantic search for RAG |
| SARIMAX .joblib | model object, order, MAPE, training window | Trained forecasting model |

### Exogenous Variables (9 columns)

| Variable | Source | Description |
|----------|--------|-------------|
| meralco_rate | Meralco S3 PDF | ₱/kWh residential electricity rate |
| avg_temperature | Open-Meteo API | Monthly average temperature (°C) |
| avg_humidity | Open-Meteo API | Monthly average relative humidity (%) |
| total_rainfall_mm | Open-Meteo API | Total monthly rainfall (mm) |
| holiday_count | Calendar data | Number of public holidays in the month |
| weekend_count | Calendar data | Number of Saturday/Sunday days |
| hot_days_count | Open-Meteo API | Days with temperature > threshold |
| rainy_days_count | Open-Meteo API | Days with measurable rainfall |
| is_el_nino | NOAA ONI | Binary indicator (1 = El Niño active) |

---

## 8. Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | July 2026 | Development Team | Initial document creation |
