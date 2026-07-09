# Traceability Matrix — WATT-IF

**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## 1. Introduction

This Requirements Traceability Matrix (RTM) maps each functional requirement to its module, implementation, and test case(s). The system is organized into 7 modules.

---

## 2. Legend

| Column | Description |
|--------|-------------|
| Req ID | From Functional_Requirements.md (FR-X.XX format) |
| Module | One of the 7 system modules |
| Implementation | Source file(s) |
| Test Case(s) | Test case ID(s) from TC_ documents |
| Status | Implemented / Partial / Not Started |

---

## 3. Module 1: Account System

| Req ID | Requirement Summary | Implementation | Test Case(s) | Status |
|--------|-------------------|----------------|--------------|--------|
| FR-1.01 | User registration | `api/auth.py` (POST /auth/register) | ACT-01 | Implemented |
| FR-1.02 | Email format validation | `api/auth.py` (_validate_email) | ACT-05 | Implemented |
| FR-1.03 | Password min 8 chars | `api/auth.py` (RegisterRequest) | ACT-03 | Implemented |
| FR-1.04 | Password confirmation match | `frontend/src/pages/RegisterPage.tsx` | ACT-04 | Implemented |
| FR-1.05 | Duplicate email rejection | `api/auth.py` (POST /auth/register) | ACT-02 | Implemented |
| FR-1.06 | Bcrypt cost 12 | `api/auth.py` (BCRYPT_COST_FACTOR) | — | Implemented |
| FR-1.07 | JWT 24h expiry | `api/auth.py` (POST /auth/login) | ACT-06 | Implemented |
| FR-1.08 | Generic error for invalid creds | `api/auth.py` | ACT-07, ACT-08 | Implemented |
| FR-1.09 | Timing-attack mitigation | `api/auth.py` (_DUMMY_HASH) | ACT-08 | Implemented |
| FR-1.10 | Rate limiting (10/15min) | `api/rate_limiter.py` | ACT-09 | Implemented |
| FR-1.11 | Reset counter on success | `api/rate_limiter.py` | ACT-09 | Implemented |
| FR-1.12 | Default account seeding | `storage/db.py` (_run_migrations) | ACT-06 | Implemented |
| FR-1.13 | Auto-login default account | `frontend/src/context/AuthContext.tsx` | ACT-06 | Implemented |
| FR-1.14 | Change password | `api/auth.py` (POST /auth/change-password) | ACT-21 | Implemented |
| FR-1.15 | Reject invalid password change | `api/auth.py` | ACT-22 | Implemented |
| FR-1.16 | Clear token on 401 | `frontend/src/api/client.ts` | ACT-14 | Implemented |
| FR-1.17 | Auth guard redirect | `frontend/src/components/AuthGuard.tsx` | ACT-19 | Implemented |
| FR-1.18 | Block auth pages for logged-in | `frontend/src/App.tsx` | ACT-20 | Implemented |

---

## 4. Module 2: Data Management

| Req ID | Requirement Summary | Implementation | Test Case(s) | Status |
|--------|-------------------|----------------|--------------|--------|
| FR-2.01 | Manual entry (month + kWh) | `api/main.py` (POST /data-entries) | DM-01 | Implemented |
| FR-2.02 | Reject invalid kWh | `api/schemas.py` (DataEntryCreate) | DM-02 to DM-05, DM-08 | Implemented |
| FR-2.03 | Accept kWh 1–1,000,000 | `api/schemas.py` | DM-06, DM-07 | Implemented |
| FR-2.04 | Reject duplicate month | `api/main.py` | DM-12 | Implemented |
| FR-2.05 | Optional bill/rate overrides | `api/schemas.py` | DM-09, DM-10 | Implemented |
| FR-2.06 | Live bill preview | `frontend/src/pages/DataEntryPage.tsx` | DM-11 | Implemented |
| FR-2.07 | Auto-resolve exog variables | `api/main.py`, `pipeline/feature_engineering.py` | DM-01 | Implemented |
| FR-2.08 | CSV upload (max 10 MB) | `api/main.py` (POST /upload) | DM-13, DM-14 | Implemented |
| FR-2.09 | Minimum + extended schema | `pipeline/data_pipeline.py` | DM-13, DM-14 | Implemented |
| FR-2.10 | Validate dates, impute, dedupe | `pipeline/data_pipeline.py` | DM-17, DM-18, DM-19 | Implemented |
| FR-2.11 | Cleaning report | `api/schemas.py` (UploadResponse) | DM-13 | Implemented |
| FR-2.12 | Reject unsafe filenames | `api/main.py` (_is_safe_filename) | DM-15 | Implemented |
| FR-2.13 | Paginated history (10/page) | `frontend/src/pages/DataEntryPage.tsx` | DM-32, DM-33 | Implemented |
| FR-2.14 | Inline edit kWh/bill | `api/main.py` (PUT /data-entries/{id}) | DM-22 to DM-25 | Implemented |
| FR-2.15 | Delete with confirmation | `api/main.py` (DELETE /data-entries/{id}) | DM-28 to DM-30 | Implemented |
| FR-2.16 | Ownership verification (403) | `api/main.py` | ACT-17 | Implemented |
| FR-2.17 | Pagination controls | `frontend/src/pages/DataEntryPage.tsx` | DM-34, DM-35 | Implemented |
| FR-2.18 | Train on button click only | `api/main.py` (POST /retrain) | DM-36 | Implemented |
| FR-2.19 | Min 14 data points | `model/sarimax_model.py` | DM-37, DM-38 | Implemented |
| FR-2.20 | 9 exog, auto_arima, 80/10/10 | `model/sarimax_model.py` | DM-36 | Implemented |
| FR-2.21 | Live training status + metrics | `api/main.py` (GET /status, /model-info) | DM-36 | Implemented |
| FR-2.22 | Prevent concurrent training | `api/main.py` | DM-39 | Implemented |
| FR-2.23 | Per-user model storage | `api/main.py` | ACT-18 | Implemented |
| FR-2.24 | Clear All Data confirmation | `frontend/src/pages/DataEntryPage.tsx` | DM-40 | Implemented |
| FR-2.25 | Delete all user data | `api/main.py` (DELETE /data/all) | DM-40 | Implemented |
| FR-2.26 | 503 after clearing | `api/main.py` (POST /forecast) | DM-40, FD-10 | Implemented |

---

## 5. Module 3: Forecasting & Dashboard

| Req ID | Requirement Summary | Implementation | Test Case(s) | Status |
|--------|-------------------|----------------|--------------|--------|
| FR-3.01 | Forecast 1/3/6/9/12 months | `model/sarimax_model.py` | FD-01 to FD-05 | Implemented |
| FR-3.02 | kWh bar chart with CI bars | `frontend/src/components/ForecastChart.tsx` | FD-07 | Implemented |
| FR-3.03 | Bill line chart with CI band | `frontend/src/components/ForecastChart.tsx` | FD-08 | Implemented |
| FR-3.04 | Bill = kwh × rate | `model/sarimax_model.py` | FD-01 | Implemented |
| FR-3.05 | Anchor from latest data | `model/sarimax_model.py` | FD-06 | Implemented |
| FR-3.06 | Month-aware fallback exog | `model/sarimax_model.py` | FD-01 | Implemented |
| FR-3.07 | Tooltips on hover | `frontend/src/components/ForecastChart.tsx` | FD-09 | Implemented |
| FR-3.08 | 503 if no model | `api/main.py` | FD-10, FD-11 | Implemented |
| FR-3.09 | Persist forecasts per user | `api/main.py` (POST/GET /saved-forecast) | FD-01 | Implemented |
| FR-3.10 | Threshold warnings | `api/main.py` | SET-12 | Implemented |
| FR-3.11 | Four stat cards | `frontend/src/pages/DashboardPage.tsx` | FD-12 | Implemented |
| FR-3.12 | Anomaly detection (>110%) | `frontend/src/pages/DashboardPage.tsx` | FD-17, FD-18 | Implemented |
| FR-3.13 | Dashboard forecast chart | `frontend/src/pages/DashboardPage.tsx` | FD-19 | Implemented |
| FR-3.14 | Loading/empty states | `frontend/src/pages/DashboardPage.tsx` | FD-16, FD-20 | Implemented |

---

## 6. Module 4: Chat Assistant

| Req ID | Requirement Summary | Implementation | Test Case(s) | Status |
|--------|-------------------|----------------|--------------|--------|
| FR-4.01 | Natural-language questions | `rag/rag_service.py` | CHT-01 | Implemented |
| FR-4.02 | ChromaDB + EDA retrieval | `rag/rag_service.py` | CHT-01, CHT-02 | Implemented |
| FR-4.03 | SSE streaming from Ollama | `api/main.py` (POST /ask) | CHT-01 | Implemented |
| FR-4.04 | 1–500 char limit | `api/schemas.py` (AskRequest) | CHT-05, CHT-06 | Implemented |
| FR-4.05 | Reject out-of-scope | `rag/rag_service.py` (_is_in_scope) | CHT-03 | Implemented |
| FR-4.06 | Per-user chat history | `api/main.py` (chat-history endpoints) | CHT-07, CHT-11 | Implemented |
| FR-4.07 | Clear Chat button | `frontend/src/components/ChatPanel.tsx` | CHT-08, CHT-09 | Implemented |
| FR-4.08 | Full-horizon context | `rag/rag_service.py` | CHT-02 | Implemented |
| FR-4.09 | Error when Ollama offline | `rag/rag_service.py` | CHT-10 | Implemented |
| FR-4.10 | Plain conversational format | `rag/rag_service.py` (_SYSTEM_PROMPT) | CHT-01 | Implemented |
| FR-4.11 | EDA summary generation | `data/eda.py`, `data/ingest_eda.py` | — | Implemented |

---

## 7. Module 5: Price Calculator

| Req ID | Requirement Summary | Implementation | Test Case(s) | Status |
|--------|-------------------|----------------|--------------|--------|
| FR-5.01 | Fetch Meralco rate PDF | `scraper/meralco_rate.py` | PCT-01 | Implemented |
| FR-5.02 | 24h cache + manual refresh | `scraper/meralco_rate.py`, `api/main.py` | PCT-12 | Implemented |
| FR-5.03 | 3 customer types | `scraper/meralco_rate.py` | PCT-11 | Implemented |
| FR-5.04 | Auto bracket selection | `scraper/meralco_rate.py` (get_bracket_for_kwh) | PCT-07 to PCT-09 | Implemented |
| FR-5.05 | Manual bracket override | `frontend/src/pages/PriceCalculatorPage.tsx` | PCT-10 | Implemented |
| FR-5.06 | Full bill breakdown | `api/main.py` (GET /meralco-rate) | PCT-02 | Implemented |
| FR-5.07 | Pre-select from settings | `frontend/src/pages/PriceCalculatorPage.tsx` | SET-03 | Implemented |

---

## 8. Module 6: Settings

| Req ID | Requirement Summary | Implementation | Test Case(s) | Status |
|--------|-------------------|----------------|--------------|--------|
| FR-6.01 | Customer type config | `api/main.py` (PUT /settings) | SET-03 | Implemented |
| FR-6.02 | Default forecast horizon | `api/schemas.py` (UserSettingsUpdate) | SET-04 | Implemented |
| FR-6.03 | Rate override (max 100) | `api/schemas.py` | SET-05, SET-06, SET-07 | Implemented |
| FR-6.04 | Chat preferences | `api/schemas.py` | SET-08, SET-09 | Implemented |
| FR-6.05 | Notification thresholds | `api/schemas.py` | SET-12, SET-13 | Implemented |
| FR-6.06 | Auto-retrain + min points | `api/schemas.py` | SET-14, SET-15 | Implemented |
| FR-6.07 | Clear chat/data actions | `api/main.py` | SET-10, SET-11 | Implemented |
| FR-6.08 | Defaults for new users | `api/main.py` (GET /settings) | SET-01 | Implemented |
| FR-6.09 | Input boundaries + persistence | `frontend/src/pages/AccountSettingsPage.tsx` | SET-13 | Implemented |

---

## 9. Module 7: System & Infrastructure

| Req ID | Requirement Summary | Implementation | Test Case(s) | Status |
|--------|-------------------|----------------|--------------|--------|
| FR-7.01 | Per-user data isolation | `storage/db.py`, `api/main.py` | ACT-15 to ACT-18 | Implemented |
| FR-7.02 | Separate model storage + 403 | `api/main.py` | ACT-17, ACT-18 | Implemented |
| FR-7.03 | Orphaned row migration | `storage/db.py` (_run_migrations) | — | Implemented |
| FR-7.04 | Sidebar navigation links | `frontend/src/components/Sidebar.tsx` | SYS-04 | Implemented |
| FR-7.05 | Active item + 404 redirect | `frontend/src/App.tsx` | SYS-05 | Implemented |
| FR-7.06 | Mobile drawer + focus trap | `frontend/src/components/AppShell.tsx` | SYS-06 to SYS-08 | Implemented |
| FR-7.07 | Dark/light mode | `frontend/src/context/ThemeContext.tsx` | SYS-01 to SYS-03 | Implemented |
| FR-7.08 | Health endpoint | `api/main.py` (GET /health) | SYS-09 | Implemented |
| FR-7.09 | Health indicator in sidebar | `frontend/src/components/HealthIndicator.tsx` | SYS-09, SYS-10 | Implemented |
| FR-7.10 | Open-Meteo weather | `pipeline/feature_engineering.py` | — | Implemented |
| FR-7.11 | NOAA ENSO lookup | `pipeline/feature_engineering.py` | — | Implemented |
| FR-7.12 | Meralco rate with fallback | `scraper/meralco_rate.py` | PCT-13 | Implemented |
| FR-7.13 | PWA installable | `frontend/public/manifest.json`, `vite-plugin-pwa` | — | Implemented |
| FR-7.14 | Offline banner + cached data | `frontend/src/components/OfflineBanner.tsx` | SYS-11 | Implemented |
