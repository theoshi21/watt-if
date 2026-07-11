# Data Flow Diagram (DFD) — WATT-IF

**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## 1. Introduction

This document presents the Data Flow Diagrams for WATT-IF at three levels: Context (Level 0), System (Level 1), and Detailed (Level 2).

### Notation

| Symbol | Meaning |
|--------|---------|
| Rectangle | External Entity |
| Rounded Rectangle | Process |
| Open-ended Rectangle | Data Store |
| Arrow | Data Flow (labeled) |

---

## 2. Context Diagram (Level 0)

### External Entities

| Entity | Role |
|--------|------|
| User | Household electricity consumer (web/PWA) |
| Meralco S3 Bucket | Hosts PDF rate schedule documents |
| Ollama LLM | Local language model (qwen3:1.7b) for chat answers |

### Diagram

```
                    +---------------------+
                    |  Meralco S3 Bucket  |
                    +----------+----------+
                               |
                               | Rate schedule PDF
                               v
+--------+                +---------+                +----------------+
|        |  Credentials,  |         |  Prompt +      |                |
|        |  CSV, entries, |         |  context       |                |
|        | -------------> | WATT-IF | -------------> |   Ollama LLM   |
|  User  |                | System  |                |  (qwen3:1.7b)  |
|        | <------------- |         | <------------- |                |
|        |  JWT, forecasts|         |  Streamed      |                |
+--------+  answers, rates+---------+  tokens        +----------------+
```

### Data Flows

| # | From → To | Data |
|---|-----------|------|
| 1 | User → WATT-IF | Credentials, CSV files, manual entries, forecast requests, chat questions, settings |
| 2 | WATT-IF → User | JWT token, forecasts (kWh, price, 95% CI), chat answers, rate info, health status |
| 3 | Meralco S3 → WATT-IF | Rate schedule PDF |
| 4 | WATT-IF → Ollama LLM | Prompt (system + context + question) |
| 5 | Ollama LLM → WATT-IF | Streamed answer tokens |

---

## 3. Level 1 DFD

### Processes

| # | Process |
|---|---------|
| 1.0 | User Authentication |
| 2.0 | Data Ingestion & Cleaning |
| 3.0 | Feature Enrichment |
| 4.0 | SARIMAX Model Training |
| 5.0 | SARIMAX Forecasting |
| 6.0 | RAG Chat |
| 7.0 | Meralco Rate Scraper |
| 8.0 | Health Monitoring |

### Data Stores

| ID | Store |
|----|-------|
| D1 | User Database |
| D2 | Billing Records |
| D3 | Data Entry Log |
| D4 | Chat History |
| D5 | Model Artefacts |
| D6 | Forecast Vector Store |
| D7 | EDA Summary Store |
| D8 | Rate Cache |
| D9 | Saved Forecasts |
| D10 | User Settings |

### Diagram

```
+--------+                                              +---------------------+
|  User  |                                              |  Meralco S3 Bucket  |
+---+----+                                              +----------+----------+
    |                                                              |
    | Credentials                                                  | Rate PDF
    v                                                              v
+-------------------+       +------+                  +---------------------+
| 1.0 User          | <---> | D1   |                  | 7.0 Meralco Rate    |
| Authentication    |       +------+                  | Scraper             |
+--------+----------+                                 +---------+-----------+
         |                                                      |
         | JWT                                                  | Parsed rate
         v                                                      v
+--------+----------+                                      +--------+
| 2.0 Data          | ---> +------+ ---> +------+          |  D8    |
| Ingestion &       |      | D2   |      | D3   |          +---+----+
| Cleaning          |      +--+---+      +------+              |
+---------+---------+         |                                |
          |                   | Raw records         Rate -------+
          | Retrain trigger   v                       |
          |            +-------------------+          |
          +----------> | 3.0 Feature       | <--------+
                       | Enrichment        |
                       +---------+---------+
                                 |
                    Enriched     |    Future exog
                    records      |    values
                       +---------+---------+
                       v                   v
              +-------------------+  +-------------------+
              | 4.0 SARIMAX Model |  | 5.0 SARIMAX       |
              | Training          |  | Forecasting       |
              +---------+---------+  +---------+---------+
                        |                      |     |
                        v                      |     v
                   +--------+                  |  +------+  +------+
                   |  D5    | -----------------+  | D6   |  | D9   |
                   +--------+   Loaded model      +--+---+  +------+
                                                     |
                      +------+ <--------- D7         |
                      | D10  | ------+               |
                      +------+       |               v
                                     |    +-------------------+
                       Thresholds ---+--> | 6.0 RAG Chat      |
                                          +---------+---------+
                                                    |     |
                                    Prompt          |     | Messages
                                    v               v     v
                          +----------------+    +--------+   +--------+
                          |   Ollama LLM   |    |  User  |   |  D4    |
                          +----------------+    +--------+   +--------+
```

### Data Flows

| # | From → To | Data |
|---|-----------|------|
| 1 | User → 1.0 | Email, password |
| 2 | 1.0 → User | JWT token |
| 3 | 1.0 → D1 | New user record |
| 4 | D1 → 1.0 | Stored credentials |
| 5 | User → 2.0 | CSV file / manual entry |
| 6 | 2.0 → D2 | Cleaned billing rows |
| 7 | 2.0 → D3 | Entry audit record |
| 8 | 2.0 → User | Confirmation |
| 9 | D2 → 3.0 | Raw billing records |
| 10 | D8 → 3.0 | Meralco rate |
| 11 | 3.0 → 4.0 | Enriched records |
| 12 | 4.0 → D5 | Trained model (.joblib) |
| 13 | 2.0 → 4.0 | Auto-retrain trigger |
| 14 | D5 → 5.0 | Loaded model |
| 15 | D2 → 5.0 | Historical records |
| 16 | 3.0 → 5.0 | Future exogenous values |
| 17 | D8 → 5.0 | Meralco rate (for price) |
| 18 | D10 → 5.0 | Threshold settings |
| 19 | 5.0 → User | Forecast results |
| 20 | 5.0 → D6 | Forecast documents |
| 21 | 5.0 → D9 | Saved forecast |
| 22 | User → 6.0 | Chat question |
| 23 | D6 → 6.0 | Top-12 forecast docs |
| 24 | D7 → 6.0 | Top-3 EDA summaries |
| 25 | 6.0 → Ollama LLM | Prompt payload |
| 26 | Ollama LLM → 6.0 | Token stream |
| 27 | 6.0 → User | Streamed chat answer |
| 28 | 6.0 → D4 | Chat messages |
| 29 | 7.0 → Meralco S3 | HTTP request |
| 30 | Meralco S3 → 7.0 | Rate PDF |
| 31 | 7.0 → D8 | Parsed rate result |
| 32 | 7.0 → User | Rate breakdown |
| 33 | User → 8.0 | Health request |
| 34 | 8.0 → User | Health status |

### Data Store Inputs & Outputs

| Store | Written By | Read By |
|-------|-----------|---------|
| D1 User Database | 1.0 Authentication | 1.0 Authentication |
| D2 Billing Records | 2.0 Data Ingestion | 3.0 Enrichment, 4.0 Training, 5.0 Forecasting |
| D3 Data Entry Log | 2.0 Data Ingestion | User (via API) |
| D4 Chat History | 6.0 RAG Chat | 6.0 RAG Chat, User (via API) |
| D5 Model Artefacts | 4.0 Training | 5.0 Forecasting, 8.0 Health |
| D6 Forecast Vector Store | 5.0 Forecasting | 6.0 RAG Chat, 8.0 Health |
| D7 EDA Summary Store | EDA Ingestion (offline) | 6.0 RAG Chat |
| D8 Rate Cache | 7.0 Rate Scraper | 3.0 Enrichment, 5.0 Forecasting, User (via API) |
| D9 Saved Forecasts | 5.0 Forecasting | User (via API) |
| D10 User Settings | User (via API) | 5.0 Forecasting |

---

## 4. Level 2 — Process 2.0: Data Ingestion & Cleaning

### Diagram

```
+--------+                                         +--------+  +--------+
|  User  |                                         |  D2    |  |  D3    |
+---+----+                                         +----+---+  +----+---+
    |                                                   ^            ^
    |                                                   |            |
    | CSV file                                          |            |
    v                                                   |            |
+-------------------+                                   |            |
| 2.1 Validate &    |                                   |            |
| Parse CSV         |                                   |            |
+---------+---------+                                   |            |
          |                                             |            |
          | Parsed rows                                 |            |
          v                                             |            |
+---------+---------+                                   |            |
| 2.2 Clean &       |                                   |            |
| Impute            |                                   |            |
+---------+---------+                                   |            |
          |                                             |            |
          | Cleaned rows                                |            |
          v                                             |            |
+---------+---------+    Deduplicated rows              |            |
| 2.3 Deduplicate   | ---------------------------------+            |
| & Store            | ----- Entry log records ----------------------+
+---------+---------+
          |
          | Cleaning report
          v
      +--------+
      |  User  |
      +--------+

    |                                                   ^            ^
    | Manual entry                                      |            |
    v                                                   |            |
+---------+---------+    Billing record                 |            |
| 2.4 Validate      | ---------------------------------+            |
| Manual Entry      | ----- Entry record ----------------------------+
+---------+---------+
          |
          | New record signal
          v
+---------+---------+           +- - - - - - - - - -+
| 2.5 Check Auto-   | -------> | 4.0 SARIMAX       |
| Retrain            |  Trigger | Training          |
+-------------------+           +- - - - - - - - - -+
```

### Sub-processes

| # | Process | Input | Output |
|---|---------|-------|--------|
| 2.1 | Validate & Parse CSV | Raw CSV file | Parsed rows |
| 2.2 | Clean & Impute | Parsed rows | Cleaned rows |
| 2.3 | Deduplicate & Store | Cleaned rows | D2 records, D3 log, report → User |
| 2.4 | Validate Manual Entry | year_month, kWh, bill | D2 record, D3 log |
| 2.5 | Check Auto-Retrain | New record count | Trigger → 4.0 Training |

---

## 5. Level 2 — Process 5.0: SARIMAX Forecasting

### Diagram

```
+--------+                          +--------+
|  User  |                          |  D5    |
+---+----+                          +----+---+
    |                                    |
    | Forecast request (horizon)         | Loaded model
    v                                    v
+-------------------+          +---------+---------+
| 5.1 Load User     | <-------| Model Artefacts   |
| Model              |          +-------------------+
+---------+---------+
          |
          | Model object                +--------+
          v                             |  D2    |
+---------+---------+                   +----+---+
| 5.2 Compute       | <--------------------+
| Exogenous Vars     |   Historical records
+---------+---------+
          |
          | Exogenous array (9 vars x horizon)
          v
+---------+---------+
| 5.3 Generate kWh  |
| Forecast (SARIMAX) |
+---------+---------+
          |
          | kWh predictions + 95% CI    +--------+
          v                             |  D8    |
+---------+---------+                   +----+---+
| 5.4 Derive Price   | <-------------------+
| (kWh x rate)       |   Meralco rate
+---------+---------+
          |
          | ForecastMonth[]
          +------------------+
          |                  |
          v                  v
+---------+---------+  +--------+
| 5.5 Embed & Store |  |  D6    |
| in Vector Store    |->+--------+
+-------------------+
          |
          | ForecastMonth[]             +--------+
          v                             |  D10   |
+---------+---------+                   +----+---+
| 5.6 Check         | <--------------------+
| Thresholds & Warn  |   Threshold settings
+---------+---------+
          |
          | Forecast + warnings
          v
      +--------+
      |  User  |
      +--------+
```

---

## 6. Level 2 — Process 6.0: RAG Chat

### Diagram

```
+--------+                                    +----------------+
|  User  |                                    |   Ollama LLM   |
+---+----+                                    +-------+--------+
    |                                                 ^    |
    | Question                                        |    | Token stream
    v                                                 |    v
+-------------------+                                 |    |
| 6.1 Scope Check   |--- Out of scope --> User        |    |
+---------+---------+                                 |    |
          |                                           |    |
          | In-scope question                         |    |
          v                                           |    |
+---------+---------+     +--------+                  |    |
| 6.2 Retrieve       | <--| D6     |                  |    |
| Context            |    +--------+                  |    |
|                    | <--| D7     |                  |    |
+---------+---------+     +--------+                  |    |
          |                                           |    |
          | Retrieved docs                            |    |
          v                                           |    |
+---------+---------+                                 |    |
| 6.3 Build Prompt   |                                |    |
+---------+---------+                                 |    |
          |                                           |    |
          | Messages array        Prompt              |    |
          v                       |                   |    |
+---------+---------+-------------+                   |    |
| 6.4 Stream LLM    | -----------------------------------+    |
| Response           | <--------------------------------------+
+---------+---------+
          |              |
          | SSE answer   | Persisted messages
          v              v
      +--------+    +--------+
      |  User  |    |  D4    |
      +--------+    +--------+
```

---

## 7. Level 2 — Process 7.0: Meralco Rate Scraper

### Diagram

```
+--------+                              +---------------------+
|  User  |                              |  Meralco S3 Bucket  |
+---+----+                              +----------+----------+
    |                                              ^    |
    | Rate request                      HTTP GET   |    | PDF bytes
    v                                              |    v
+-------------------+                              |    |
| 7.1 Check Cache   |--- Cache hit --> User        |    |
| TTL                |                              |    |
+---------+---------+                              |    |
          |                                        |    |
          | Cache miss                             |    |
          v                                        |    |
+---------+---------+                              |    |
| 7.2 Download PDF   | ---------------------------+    |
|                    | <-------------------------------+
+---------+---------+
          |
          | PDF bytes
          v
+---------+---------+
| 7.3 Parse PDF      |
| Tables              |
+---------+---------+
          |
          | Customer types + rate brackets
          v
+---------+---------+         +--------+
| 7.4 Cache Result   | -----> |  D8    |
+---------+---------+         +--------+
          |
          | Rate breakdown
          v
      +--------+
      |  User  |
      +--------+

          (If download fails)
          |
          v
+---------+---------+         +--------+
| 7.5 Fallback       | -----> |  D8    |
| Rates              |         +--------+
+---------+---------+
          |
          | Fallback rate
          v
      +--------+
      |  User  |
      +--------+
```

---

## 8. Data Dictionary

| Data | Format | Description |
|------|--------|-------------|
| Credentials | `{email, password}` | Registration/login input |
| JWT Token | HS256 string, 24h expiry | Bearer auth token |
| CSV File | year_month, kwh, price columns | Bill history upload |
| Manual Entry | `{year_month, kwh, bill_amount}` | Single data point |
| Forecast Request | `{horizon: 1/3/6/9/12}` | Prediction horizon |
| Forecast Response | `{months: [{kwh, price, ci_lower, ci_upper}]}` | Prediction output |
| Chat Question | `{question: string}` | Natural-language query |
| Chat Answer | SSE stream (token/done/error) | LLM response |
| Rate PDF | Binary PDF | Meralco schedule of rates |

---

## 9. Document Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | July 2026 | Initial creation |
| 2.0 | July 2026 | Simplified structure; added SARIMAX Forecasting; renamed to Meralco Rate Scraper; removed phantom external APIs; added data store I/O table; added Level 2 for Rate Scraper |
