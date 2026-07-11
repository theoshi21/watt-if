# Data Flow Diagram (DFD) — WATT-IF

**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## 1. Introduction

This document presents the Data Flow Diagrams for the WATT-IF system at three levels of decomposition.

### Notation

| Symbol | Meaning |
|--------|---------|
| Rectangle | External Entity (actor) |
| Circle / Rounded Rectangle | Process |
| Cylinder / Open-ended Rectangle | Data Store |
| Arrow | Data Flow (labeled with data description) |

---

## 2. Context Diagram (Level 0)

The context diagram shows all external entities and the data exchanged with the WATT-IF system.

```
          Account information (register, login, change password)
          ---------------------------------------------------------->
          Account access (JWT token)
          <----------------------------------------------------------
          CSV upload / manual data entry (year_month, kWh, bill)
          ---------------------------------------------------------->
          Upload confirmation / data entries list
          <----------------------------------------------------------
          Forecast request (horizon: 1/3/6/9/12 months)
          ---------------------------------------------------------->
          Forecast results (kWh, price, 95% CI per month)
          <----------------------------------------------------------
          Chat question (natural-language)
+--------+---------------------------------------------------------->+--------+
|        |  Chat answer (SSE-streamed tokens)                        |        |
|        |<----------------------------------------------------------|        |
|        |  Meralco rate request                                     |        |
|        |---------------------------------------------------------->|        |
|  User  |  Rate breakdown (by customer type)                        | WATT-IF|
|        |<----------------------------------------------------------|System  |
|        |  Settings update (customer type, thresholds)              |        |
|        |---------------------------------------------------------->|   0    |
|        |  Current settings                                         |        |
|        |<----------------------------------------------------------|        |
|        |  Health check request                                     |        |
|        |---------------------------------------------------------->|        |
|        |  System health status                                     |        |
|        |<----------------------------------------------------------|        |
+--------+                                                           +---+----+
                                                                         |   ^
                                                                         |   |
                                              Prompt (context + question) |   | Streamed tokens
                                                                         v   |
                                                                     +--------+
                                                                     | Ollama |
                                                                     |  LLM   |
                                                                     +--------+

                                                                         |   ^
                                                                         |   |
                                                      HTTP request (PDF) |   | Rate schedule PDF
                                                                         v   |
                                                                     +--------+
                                                                     |Meralco |
                                                                     |S3      |
                                                                     |Bucket  |
                                                                     +--------+
```

---

## 3. Level 1 DFD

The system is decomposed into functional modules, all connected to the central System Database.

```
+-------------------+                                         +-------------------+
|       1.0         |                                         |       2.0         |
|      User         |                                         |  Data Ingestion   |
|  Authentication   |                                         |   & Cleaning      |
+--------+----------+                                         +---------+---------+
         |    ^                                                         |    ^
         |    |                                                         |    |
         |    | Retrieve credentials, user profile                      |    |
         |    | Store new user, update login timestamp                  |    |
         v    |                                                         v    |
         |    |    Store cleaned billing rows, entry log                |    |
         |    |    Retrieve existing records (dedup check)              |    |
         |    |                                                         |    |
         |    |                                                         |    |
         |    |         +===================================+           |    |
         |    +---------|                                   |-----------+    |
         +------------->|        System Database            |<--------------+
                        |         (SQLite +                 |
+-------------------+   |          ChromaDB +               |   +-------------------+
|       3.0         |   |          Filesystem)              |   |       5.0         |
|     Feature       |-->|                                   |<--|     SARIMAX       |
|   Enrichment      |<--|                                   |-->|   Forecasting     |
+-------------------+   |                                   |   +-------------------+
         |    ^         |                                   |           |    ^
         |    |         |                                   |           |    |
         |    |         |                                   |           |    |
         |    |         |                                   |           |    |
         |    |         |                                   |           |    |
+-------------------+   |                                   |   +-------------------+
|       4.0         |   |                                   |   |       6.0         |
|  SARIMAX Model    |-->|                                   |<--|    RAG Chat       |
|    Training       |<--|                                   |-->|                   |
+-------------------+   |                                   |   +-------------------+
                        |                                   |
+-------------------+   |                                   |   +-------------------+
|       7.0         |-->|                                   |<--|       8.0         |
|  Meralco Rate     |<--|                                   |-->|     Health        |
|    Scraper        |   |                                   |   |   Monitoring      |
+-------------------+   +===================================+   +-------------------+


DATA FLOWS BETWEEN MODULES AND DATABASE:

1.0 User Authentication:
  - Retrieve: user credentials, profile data
  - Store: new user record, login timestamp

2.0 Data Ingestion & Cleaning:
  - Store: cleaned billing rows, data entry log records
  - Retrieve: existing records (for deduplication)

3.0 Feature Enrichment:
  - Retrieve: raw billing records, cached Meralco rate
  - Store: enriched records (9 exogenous columns)

4.0 SARIMAX Model Training:
  - Retrieve: enriched historical records
  - Store: trained model artefact (.joblib), training log

5.0 SARIMAX Forecasting:
  - Retrieve: model artefact, historical records, rate, user settings
  - Store: forecast documents (vector store), saved forecasts

6.0 RAG Chat:
  - Retrieve: forecast documents (top-12), EDA summaries (top-3), chat history
  - Store: chat messages (user + assistant)

7.0 Meralco Rate Scraper:
  - Store: parsed rate result (in-memory cache)

8.0 Health Monitoring:
  - Retrieve: subsystem status (DB, model, ChromaDB, Ollama)
```

---

## 4. Level 2 — Process 1.0: User Authentication

```
                                       +-------------+
                              Register |     1.1     |
              +--------+ ------------->|    User     | --Store user record-->+=========+
              |        | <-------------|Registration |                       |T1       |
              |        |   Confirmation+-------------+                       | users   |
              |        |                                                     |         |
              |        |               +-------------+                       |         |
              |        |   Login       |     1.2     | --Retrieve creds----->|         |
              |  User  | ------------->|Authentication| <-Stored hash---------|         |
              |        | <-------------|             |                       |         |
              |        |   JWT token   +-------------+                       |         |
              |        |                                                     |         |
              |        |               +-------------+                       |         |
              |        | Change pwd    |     1.3     | --Verify current----->|         |
              |        | ------------->|  Password   | --Update hash-------->|         |
              |        | <-------------|  Management | <-Stored hash---------|         |
              +--------+   Confirmation+-------------+                       +=========+
```

---

## 5. Level 2 — Process 2.0: Data Ingestion & Cleaning

```
                                       +-------------+
              +--------+   CSV file    |     2.1     |
              |        | ------------->|  Validate & |
              |        |               |  Parse CSV  |
              |        |               +------+------+
              |        |                      |
              |        |                      | Parsed rows
              |        |                      v
              |        |               +-------------+
              |        |               |     2.2     |
              |        |               |  Clean &    |
              |        |               |  Impute     |
              |        |               +------+------+
              |        |                      |
              |        |                      | Cleaned rows
              |        |                      v
              |        |               +-------------+  Store billing rows   +=========+
              |        |               |     2.3     | -------------------->|T2       |
              |        |               | Deduplicate | --Store entry log--->|monthly_ |
              |  User  |               |  & Store    |                      |bill_    |
              |        | <-------------|             |                      |records  |
              |        |  Cleaning rpt +-------------+                      +=========+
              |        |
              |        |               +-------------+                      +=========+
              |        | Manual entry  |     2.4     | --Store entry------->|T3       |
              |        | ------------->|  Validate   | --Store billing----->|data_    |
              |        | <-------------|  Manual     |                      |entry_log|
              |        |  Confirmation |  Entry      |                      +=========+
              |        |               +------+------+
              |        |                      |
              +--------+                      | New record signal
                                              v
                                       +-------------+      +- - - - - - -+
                                       |     2.5     |      |     4.0     |
                                       | Check Auto- |----->| SARIMAX     |
                                       | Retrain     |      | Training    |
                                       +-------------+      +- - - - - - -+
```

---

## 6. Level 2 — Process 5.0: SARIMAX Forecasting

```
              +--------+                                              +=========+
              |        | Forecast request                              |T4       |
              |        | (horizon)              +-------------+        |sarimax_ |
              |  User  | --------------------->|     5.1     |<-------|model.   |
              |        |                       | Load User   | Load   |joblib   |
              |        |                       | Model       | model  +=========+
              |        |                       +------+------+
              |        |                              |
              |        |                              | Model object         +=========+
              |        |                              v                      |T2       |
              |        |                       +-------------+              |monthly_ |
              |        |                       |     5.2     |<-------------|bill_    |
              |        |                       | Compute     | Historical   |records  |
              |        |                       | Exogenous   | records      +=========+
              |        |                       +------+------+
              |        |                              |
              |        |                              | Exog array
              |        |                              v
              |        |                       +-------------+
              |        |                       |     5.3     |
              |        |                       | Generate kWh|
              |        |                       | Forecast    |
              |        |                       +------+------+
              |        |                              |
              |        |                              | kWh + 95% CI        +=========+
              |        |                              v                      |T5       |
              |        |                       +-------------+              |rate_    |
              |        |                       |     5.4     |<-------------|cache    |
              |        |                       | Derive Price| Meralco rate +=========+
              |        |                       +------+------+
              |        |                              |
              |        |                              | ForecastMonth[]
              |        |                              v
              |        |                       +-------------+ Store docs   +=========+
              |        |                       |     5.5     |------------>|T6       |
              |        |                       | Embed &     |             |forecast_|
              |        |                       | Store       |             |documents|
              |        |                       +------+------+             +=========+
              |        |                              |
              |        |                              v                      +=========+
              |        |                       +-------------+              |T7       |
              |        |  Forecast +           |     5.6     |<-------------|user_    |
              |        |  warnings             | Check       | Thresholds   |settings |
              |        | <--------------------|Thresholds   |              +=========+
              +--------+                       +-------------+
```

---

## 7. Level 2 — Process 6.0: RAG Chat

```
              +--------+                                             +----------+
              |        | Question                                    |  Ollama  |
              |        |               +-------------+              |   LLM    |
              |  User  | ------------>|     6.1     |              +----------+
              |        |              | Scope Check  |                  ^    |
              |        | <---Out of---|             |                  |    |
              |        |    scope     +------+------+                  |    |
              |        |                     |                         |    |
              |        |                     | In-scope                |    |
              |        |                     v                         |    |
              |        |              +-------------+ Query   +=========+  |
              |        |              |     6.2     |-------->|T6       |  |
              |        |              |  Retrieve   |<--------|forecast_|  |
              |        |              |  Context    |  Docs   |documents|  |
              |        |              |             |-------->+=========+  |
              |        |              |             |<--------+=========+  |
              |        |              +------+------+ EDA docs|T8       |  |
              |        |                     |                |eda_     |  |
              |        |                     | Docs           |summaries|  |
              |        |                     v                +=========+  |
              |        |              +-------------+                      |
              |        |              |     6.3     |                      |
              |        |              | Build Prompt |                      |
              |        |              +------+------+                      |
              |        |                     |                             |
              |        |                     | Messages array    Prompt    |
              |        |                     v                     |       |
              |        |              +-------------+ ----------->+       |
              |        |              |     6.4     |                      |
              |        |  SSE answer  | Stream LLM  | <-- Token stream ---+
              |        | <------------|  Response   |
              |        |              +------+------+
              +--------+                     |
                                             | Store messages
                                             v
                                       +=========+
                                       |T9       |
                                       |chat_    |
                                       |history  |
                                       +=========+
```

---

## 8. Level 2 — Process 7.0: Meralco Rate Scraper

```
              +--------+                                             +----------+
              |        | Rate request                                | Meralco  |
              |        |               +-------------+              | S3       |
              |  User  | ------------>|     7.1     |              | Bucket   |
              |        |              | Check Cache  |              +----------+
              |        | <--Cache hit-|  TTL        |                  ^    |
              |        |              +------+------+                  |    |
              |        |                     |                         |    |
              |        |                     | Cache miss              |    |
              |        |                     v                         |    |
              |        |              +-------------+ HTTP GET         |    |
              |        |              |     7.2     |---------------->+    |
              |        |              | Download    |<-- PDF bytes --------+
              |        |              |  PDF        |
              |        |              +------+------+
              |        |                     |
              |        |                     | PDF bytes
              |        |                     v
              |        |              +-------------+
              |        |              |     7.3     |
              |        |              | Parse PDF   |
              |        |              | Tables      |
              |        |              +------+------+
              |        |                     |
              |        |                     | Parsed rates
              |        |                     v
              |        |              +-------------+  Store    +=========+
              |        |  Rate        |     7.4     |--------->|T5       |
              |        |  breakdown   | Cache       |          |rate_    |
              |        | <------------|  Result     |          |cache    |
              |        |              +-------------+          +=========+
              |        |
              |        |              +-------------+  Store    +=========+
              |        |  Fallback    |     7.5     |--------->|T5       |
              |        |  rate        | Fallback    |          |rate_    |
              |        | <------------|  Rates      |          |cache    |
              +--------+              +-------------+          +=========+
                                      (if download fails)
```

---

## 9. Data Dictionary

| Data | Description |
|------|-------------|
| Credentials | Email + password for registration/login |
| JWT Token | HS256 bearer token, 24h expiry |
| CSV File | Monthly bill history (year_month, kwh, price columns) |
| Manual Entry | Single data point (year_month, kwh, bill_amount) |
| Forecast Request | Prediction horizon (1, 3, 6, 9, or 12 months) |
| Forecast Response | kWh, price, CI lower/upper per forecasted month |
| Chat Question | Natural-language query about electricity bills |
| Chat Answer | SSE-streamed LLM response (token/done/error events) |
| Rate PDF | Meralco Summary Schedule of Rates (binary PDF) |
| Rate Breakdown | Parsed rates by customer type and kWh bracket |

---

## 10. Database Tables Referenced

| ID | Table | Key Fields |
|----|-------|-----------|
| T1 | `users` | id, email, password_hash, created_at |
| T2 | `monthly_bill_records` | user_id, year_month, kwh, price, 9 exog columns |
| T3 | `data_entry_log` | id, user_id, year_month, kwh, bill_amount, source |
| T4 | `sarimax_model.joblib` | Per-user trained model file |
| T5 | `rate_cache` (in-memory) | MeralcoRateResult, 24h TTL |
| T6 | `forecast_documents` (ChromaDB) | Forecast embeddings, user-scoped |
| T7 | `user_settings` | user_id, customer_type, thresholds |
| T8 | `eda_summaries` (ChromaDB) | 17 EDA narrative documents |
| T9 | `chat_history` | id, user_id, role, text, created_at |
| T10 | `saved_forecasts` | user_id, horizon, months (JSON) |

---

## 11. Document Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | July 2026 | Initial creation |
| 2.0 | July 2026 | Restructured to follow standard DFD conventions (Level 0: actors + I/O, Level 1: modules + central DB, Level 2: sub-processes + tables); simplified content; added all Level 2 decompositions |
