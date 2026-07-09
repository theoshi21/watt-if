# Functional Requirements — WATT-IF

**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## 1. Introduction

This document defines all functional requirements for WATT-IF, a locally-hosted Progressive Web App for forecasting household electricity consumption and cost in the Philippines. Requirements are organized into 7 modules that reflect the major functional areas of the system.

### Module Overview

| Module | Description |
|--------|-------------|
| 1. Account System | Registration, login, JWT authentication, password management, rate limiting |
| 2. Data Management | Manual entry, CSV upload, entry history (edit/delete/pagination), model training, clear all data |
| 3. Forecasting & Dashboard | Forecast generation, charts, confidence intervals, stat cards, anomaly detection |
| 4. Chat Assistant | RAG questions, streaming responses, history, EDA retrieval, scope filtering |
| 5. Price Calculator | Meralco rate scraping, bracket selection, bill breakdown |
| 6. Settings | User preferences, notification thresholds, data/privacy controls |
| 7. System & Infrastructure | Auth guards, per-user isolation, navigation/routing, health monitoring, PWA/offline, external APIs, database |

---

## 2. Module 1: Account System

| ID | Requirement |
|----|-------------|
| FR-1.01 | The system SHALL allow users to register a new account by providing an email address, password, and password confirmation. |
| FR-1.02 | The system SHALL validate that the registration email contains exactly one "@" symbol, a non-empty local part, a domain containing at least one ".", and does not exceed 254 characters. |
| FR-1.03 | The system SHALL reject registration if the password is fewer than 8 characters. |
| FR-1.04 | The system SHALL reject registration if the password and confirmation password do not match. |
| FR-1.05 | The system SHALL reject registration if the email is already registered (HTTP 409). |
| FR-1.06 | The system SHALL hash passwords using bcrypt with a cost factor of 12 before storing them. |
| FR-1.07 | The system SHALL issue a JSON Web Token (JWT) with a 24-hour expiry upon successful login. |
| FR-1.08 | The system SHALL return an identical generic error message for both invalid email and invalid password login attempts. |
| FR-1.09 | The system SHALL perform a dummy bcrypt comparison for non-existent email logins (timing-attack mitigation). |
| FR-1.10 | The system SHALL enforce login rate limiting: max 10 failed attempts per email within a 15-minute window (HTTP 429). |
| FR-1.11 | The system SHALL reset the failed login counter upon successful authentication. |
| FR-1.12 | The system SHALL seed a default account (`wattif@gmail.com` / `wattif`) on first database initialization. |
| FR-1.13 | The system SHALL auto-login with the default account if no additional user accounts exist. |
| FR-1.14 | The system SHALL provide a "Change Password" feature requiring current password, new password (≥8 chars), and confirmation. |
| FR-1.15 | The system SHALL reject a password change if the current password is incorrect or if new/confirm don't match. |
| FR-1.16 | The system SHALL clear the stored token and redirect to login upon receiving HTTP 401 from the API. |
| FR-1.17 | The system SHALL redirect unauthenticated users to the login page for any protected route. |
| FR-1.18 | The system SHALL prevent authenticated users from accessing the Login and Register pages. |

---

## 3. Module 2: Data Management

### 3.1 Manual Entry

| ID | Requirement |
|----|-------------|
| FR-2.01 | The system SHALL allow users to manually enter a monthly electricity reading by specifying a month (YYYY-MM) and kWh consumed. |
| FR-2.02 | The system SHALL reject manual entries where kWh is blank, zero, negative, non-numeric, or exceeds 1,000,000. |
| FR-2.03 | The system SHALL accept kWh values between 1 and 1,000,000 (inclusive). |
| FR-2.04 | The system SHALL reject a manual entry if a record for the specified month already exists for that user. |
| FR-2.05 | The system SHALL allow optional bill amount override (≥ ₱0) and rate override (> ₱0/kWh). |
| FR-2.06 | The system SHALL display a live bill preview (kWh × current rate) as the user types. |
| FR-2.07 | The system SHALL auto-resolve exogenous variables for each entry: Meralco rate, temperature, humidity, rainfall, holiday count, weekend count, hot days, rainy days, and ENSO phase. |

### 3.2 CSV Upload

| ID | Requirement |
|----|-------------|
| FR-2.08 | The system SHALL allow users to upload a CSV file containing historical bill data (max 10 MB). |
| FR-2.09 | The system SHALL accept a minimum schema of `year_month`, `kwh`, `price` and an extended schema with 9 additional exogenous columns. |
| FR-2.10 | The system SHALL validate YYYY-MM date format, impute missing optional values, and remove duplicate months. |
| FR-2.11 | The system SHALL return a cleaning report (rows received, imputed, duplicates removed, final count). |
| FR-2.12 | The system SHALL reject filenames containing path traversal patterns or special characters. |

### 3.3 Entry History

| ID | Requirement |
|----|-------------|
| FR-2.13 | The system SHALL display all entries in a paginated table (10 rows/page) with resolved exogenous values. |
| FR-2.14 | The system SHALL allow inline editing of kWh and bill amount for existing entries. |
| FR-2.15 | The system SHALL allow deletion of entries with a confirmation step. |
| FR-2.16 | The system SHALL verify ownership before edit/delete operations (HTTP 403 if unauthorized). |
| FR-2.17 | The system SHALL display pagination controls (next, previous, first, last) when entries exceed 10, and hide them otherwise. |

### 3.4 Model Training

| ID | Requirement |
|----|-------------|
| FR-2.18 | The system SHALL train the SARIMAX model only when the user explicitly clicks "Train Model." |
| FR-2.19 | The system SHALL require a minimum of 14 data points (configurable 3–60 via settings) before training. |
| FR-2.20 | The system SHALL use 9 exogenous variables and auto_arima for order selection with an 80/10/10 chronological split. |
| FR-2.21 | The system SHALL display live training status (Idle → Training → Done/Failed) and evaluation metrics after completion. |
| FR-2.22 | The system SHALL prevent concurrent training sessions for the same user. |
| FR-2.23 | The system SHALL store the trained model per user in `data/models/<user_id>/`. |

### 3.5 Clear All Data

| ID | Requirement |
|----|-------------|
| FR-2.24 | The system SHALL provide a "Clear All Data" action with a confirmation step. |
| FR-2.25 | Upon confirmation, the system SHALL delete all of the user's bill records, entries, chat history, model artefact, and saved forecasts. |
| FR-2.26 | The system SHALL return HTTP 503 on forecast attempts after clearing (until retraining). |

---

## 4. Module 3: Forecasting & Dashboard

### 4.1 Forecasting

| ID | Requirement |
|----|-------------|
| FR-3.01 | The system SHALL generate SARIMAX forecasts for horizons of 1, 3, 6, 9, or 12 months. |
| FR-3.02 | The system SHALL display kWh forecasts as a bar chart with 95% confidence interval error bars. |
| FR-3.03 | The system SHALL display bill forecasts as a line chart with a shaded 95% CI band. |
| FR-3.04 | The system SHALL calculate the forecasted bill as predicted_kwh × meralco_rate. |
| FR-3.05 | The system SHALL anchor forecasts forward from the most recent data point. |
| FR-3.06 | The system SHALL use month-aware fallback exogenous values when no explicit future inputs are provided. |
| FR-3.07 | The system SHALL display tooltips with values when hovering over chart elements. |
| FR-3.08 | The system SHALL return HTTP 503 with a user-friendly message if no trained model exists. |
| FR-3.09 | The system SHALL persist generated forecasts per user and restore them on login. |
| FR-3.10 | The system SHALL include threshold warnings when forecasted values exceed user notification settings. |

### 4.2 Dashboard

| ID | Requirement |
|----|-------------|
| FR-3.11 | The system SHALL display four stat cards: This Month kWh, Daily Average, Avg Temperature, Avg Humidity. |
| FR-3.12 | The system SHALL detect and display an anomaly alert when first forecast month exceeds 110% of the mean. |
| FR-3.13 | The system SHALL display the forecast chart on the dashboard (shared state with Forecast page). |
| FR-3.14 | The system SHALL display loading skeletons while data is fetching, and an empty state when no forecast exists. |

---

## 5. Module 4: Chat Assistant

| ID | Requirement |
|----|-------------|
| FR-4.01 | The system SHALL allow users to ask natural-language questions about their electricity forecasts and usage. |
| FR-4.02 | The system SHALL retrieve forecast documents from ChromaDB (top-k=12) and EDA summaries (top-k=3) as context. |
| FR-4.03 | The system SHALL stream responses from Ollama (Qwen3 1.7B) using Server-Sent Events (SSE). |
| FR-4.04 | The system SHALL limit question input to 1–500 characters. |
| FR-4.05 | The system SHALL reject out-of-scope questions before sending to the LLM. |
| FR-4.06 | The system SHALL persist chat messages per user and load history (up to 100 messages) on page mount. |
| FR-4.07 | The system SHALL provide a "Clear Chat" button that wipes messages from UI and database. |
| FR-4.08 | The system SHALL use full-horizon context from the most recently generated forecast. |
| FR-4.09 | The system SHALL display a graceful error when Ollama is unavailable. |
| FR-4.10 | The system SHALL format responses in plain conversational language (no headers, no emoji). |
| FR-4.11 | The system SHALL generate and ingest EDA narrative summaries into ChromaDB for RAG retrieval. |

---

## 6. Module 5: Price Calculator

| ID | Requirement |
|----|-------------|
| FR-5.01 | The system SHALL fetch the current Meralco Summary Schedule of Rates from the official PDF. |
| FR-5.02 | The system SHALL cache fetched rate data for 24 hours and allow manual refresh. |
| FR-5.03 | The system SHALL support three customer types: Residential, General Service A, General Service B. |
| FR-5.04 | The system SHALL automatically select the correct consumption bracket based on kWh input. |
| FR-5.05 | The system SHALL allow manual bracket override by the user. |
| FR-5.06 | The system SHALL display a full bill breakdown: generation, transmission, system loss, distribution, supply, metering, and other charges (VAT-inclusive). |
| FR-5.07 | The system SHALL pre-select the customer type from the user's saved settings. |

---

## 7. Module 6: Settings

| ID | Requirement |
|----|-------------|
| FR-6.01 | The system SHALL allow users to configure customer type (Residential, General Service A, General Service B). |
| FR-6.02 | The system SHALL allow users to set a default forecast horizon (1, 3, 6, 9, or 12 months). |
| FR-6.03 | The system SHALL allow users to set a rate override (₱/kWh, max 100) that bypasses the live scraper. |
| FR-6.04 | The system SHALL allow users to configure chat preferences: max history (10–500) and auto-clear on logout. |
| FR-6.05 | The system SHALL allow users to set notification thresholds: kWh budget (0–99,999), bill ceiling (0–999,999), and high consumption warning (0–99,999). |
| FR-6.06 | The system SHALL allow users to toggle auto-retrain on CSV upload and configure minimum data points (3–60). |
| FR-6.07 | The system SHALL provide "Clear Chat History" and "Clear All Data" actions with confirmation steps. |
| FR-6.08 | The system SHALL return default settings for new users and accept partial updates. |
| FR-6.09 | The system SHALL enforce input boundaries and persist all settings across navigation and refresh. |

---

## 8. Module 7: System & Infrastructure

### 8.1 Per-User Data Isolation

| ID | Requirement |
|----|-------------|
| FR-7.01 | All bill records, entries, chat history, training logs, and saved forecasts SHALL be scoped to the authenticated user. |
| FR-7.02 | Each user's model SHALL be stored separately; attempting to access another user's data SHALL return HTTP 403. |
| FR-7.03 | Orphaned rows (NULL user_id) SHALL be assigned to the default account during migration. |

### 8.2 Navigation & UI Shell

| ID | Requirement |
|----|-------------|
| FR-7.04 | The system SHALL provide a sidebar with links to Dashboard, Forecast, Ask WATT-IF, Price Calculator, Data Entry, and Account Settings. |
| FR-7.05 | The system SHALL highlight the active navigation item and redirect unknown routes to Dashboard. |
| FR-7.06 | The system SHALL provide a mobile hamburger menu with drawer, overlay dismiss, Escape key close, and focus trap. |
| FR-7.07 | The system SHALL support dark/light mode toggle persisted to localStorage. |

### 8.3 Health Monitoring

| ID | Requirement |
|----|-------------|
| FR-7.08 | The system SHALL expose a GET /health endpoint reporting status of: data pipeline, SARIMAX model, vector store, and LLM service. |
| FR-7.09 | The system SHALL display health indicators in the sidebar, polling periodically. |

### 8.4 External Integrations

| ID | Requirement |
|----|-------------|
| FR-7.10 | The system SHALL fetch weather data from Open-Meteo API for Metro Manila. |
| FR-7.11 | The system SHALL fetch ENSO phase from the NOAA ONI index. |
| FR-7.12 | The system SHALL fetch Meralco rates from the S3 PDF and fall back gracefully when unavailable. |

### 8.5 PWA & Offline

| ID | Requirement |
|----|-------------|
| FR-7.13 | The system SHALL be installable as a PWA on desktop and mobile devices. |
| FR-7.14 | The system SHALL display an offline banner when network connectivity is lost and serve cached data. |
