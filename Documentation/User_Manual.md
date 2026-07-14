# User Manual — WATT-IF

**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [System Requirements](#2-system-requirements)
3. [Interface Requirements](#3-interface-requirements)
4. [Installation and Setup Guide](#4-installation-and-setup-guide)
5. [Deployment to Production](#5-deployment-to-production)
6. [WATT-IF Interface](#6-watt-if-interface)
7. [Accessibility Features](#7-accessibility-features)
8. [Existing Bugs and How to Resolve](#8-existing-bugs-and-how-to-resolve)

---

## 1. Getting Started

### What is WATT-IF?

WATT-IF is a locally-hosted Progressive Web App (PWA) designed for forecasting household electricity consumption and cost in the Philippines. It uses a SARIMAX time-series model with 9 exogenous weather and calendar variables to predict your electricity usage 1 to 12 months into the future.

### What Can You Do With WATT-IF?

- **Upload or manually enter** your monthly electricity bill history
- **Generate forecasts** for 1, 3, 6, 9, or 12 months ahead with 95% confidence intervals
- **Ask natural-language questions** about your energy usage via the built-in AI chat assistant
- **Calculate your Meralco bill** using the latest rate schedule with a full breakdown by charge component
- **Monitor anomalies** — get alerted when forecasted consumption is unusually high
- **Install as an app** on your desktop or mobile phone (PWA-capable)

### How It Works

1. You provide historical electricity data (via CSV upload or manual entry)
2. The system auto-resolves exogenous variables (weather, Meralco rates, holidays, ENSO status)
3. You train the SARIMAX model on your data
4. The system generates forecasts and ingests them into a vector store
5. You can ask questions about your forecast using the RAG-powered chat assistant

### First-Time Use

On first launch, WATT-IF auto-logs in with a default account:

- **Email:** `wattif@gmail.com`
- **Password:** `wattif`

You can register your own account from the login page at any time. Each account has fully isolated data — your bills, forecasts, model, and chat history are private to your account.

---

## 2. System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Dual-core 2.0 GHz | Quad-core 3.0 GHz+ |
| RAM | 4 GB | 8 GB+ |
| Storage | 2 GB free | 5 GB free (for Ollama model) |
| Network | None (runs locally) | LAN for mobile PWA access |

### Software Requirements

| Software | Version | Purpose | Required? |
|----------|---------|---------|-----------|
| Python | 3.10 or later | Backend server, model training, data pipeline | Yes |
| Node.js | 18 or later | Frontend build and development server | Yes |
| npm | 9 or later (comes with Node.js) | Package management for frontend | Yes |
| Ollama | Latest | Local LLM for the RAG chat assistant | Only for chat feature |
| Web Browser | Chrome 100+, Firefox 100+, Edge 100+, Safari 16+ | Frontend interface | Yes |

### Operating System Compatibility

| OS | Supported |
|----|-----------|
| Windows 10/11 | ✔ Fully supported |
| macOS 12+ | ✔ Fully supported |
| Linux (Ubuntu 22.04+) | ✔ Fully supported |
| Android (Chrome) | ✔ PWA installable over HTTP on LAN |
| iOS (Safari) | ⚠ PWA install requires HTTPS |

### Network Requirements

- No internet connection is required for core functionality (upload, train, forecast)
- Internet is needed for:
  - Live Meralco rate scraping (falls back to cached rates if offline)
  - Open-Meteo weather data resolution
  - NOAA ENSO phase lookup
  - Downloading Ollama models (one-time)

---

## 3. Interface Requirements

### Browser Requirements

- JavaScript enabled
- Cookies / localStorage enabled (for auth tokens, theme preference)
- Minimum viewport width: 360px (mobile), 1024px recommended (desktop)
- Service Worker support (for PWA features and offline caching)

### Backend Ports

| Service | Port | Protocol |
|---------|------|----------|
| FastAPI backend | 8000 | HTTP |
| Vite dev server | 5173 | HTTP |
| Vite preview server | 4173 | HTTP |
| Ollama LLM service | 11434 | HTTP |

### API Communication

- The frontend communicates with the backend via REST API over HTTP
- Authentication uses JWT Bearer tokens in the `Authorization` header
- The RAG chat feature uses Server-Sent Events (SSE) for streaming responses
- CORS is auto-configured for localhost and LAN IP

---

## 4. Installation and Setup Guide

### Step 1 — Clone or Download the Project

Place the project in your desired directory. Example:

```
C:\Users\<your-username>\Desktop\WATT-IF
```

### Step 2 — Install Python Dependencies

Open a terminal in the project root directory.

**Option A — Global install:**

```bash
pip install -r requirements.txt
```

**Option B — Virtual environment (recommended):**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Step 3 — Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

Edit `.env` and set a strong JWT secret:

```
JWT_SECRET=your-strong-random-secret-here
```

> For local development, the default value `dev-secret-change-in-production` is used if not set.

### Step 4 — Install Ollama (Optional — for chat feature)

1. Download Ollama from **https://ollama.com/download/windows**
2. Run `OllamaSetup.exe` — it installs silently and starts as a background service
3. Open a new terminal and pull the language model:

```bash
ollama pull qwen3:1.7b
```

> The chat feature requires ~2 GB of disk space for the model. All other features (upload, forecast, price calculator) work without Ollama.

### Step 5 — Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 6 — Start the Application

You need **two terminal windows** running simultaneously:

**Terminal 1 — Backend (FastAPI)**

From the project root:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

> Important: Always run this command from the project root folder (the one containing `api/`, `model/`, `pipeline/`, etc.)

**Terminal 2 — Frontend (React)**

From the `frontend/` directory:

```bash
npm run dev
```

### Step 7 — Open the Application

Open your browser and navigate to:

```
http://localhost:5173
```

The app is ready. On first launch, you'll be automatically logged in with the default account.

---

## 5. Deployment to Production

### Local Network Deployment (LAN Access)

This allows other devices on your Wi-Fi network (phones, tablets, other PCs) to access WATT-IF.

**Step 1 — Find your PC's local IP address**

Windows (PowerShell):
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch '^(127\.|169\.)' } | Select-Object IPAddress
```

macOS / Linux:
```bash
hostname -I | awk '{print $1}'
```

You'll get an IP like `192.168.1.x`.

**Step 2 — Create `frontend/.env.local`** (if overriding auto-detection)

```
VITE_API_BASE=http://192.168.1.x:8000
```

> Note: The backend auto-detects your LAN IP for CORS configuration. You only need `.env.local` if auto-detection doesn't work for your network.

**Step 3 — Start the backend on all interfaces**

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Step 4 — Build and serve the frontend**

```bash
cd frontend
npm run build
npm run preview -- --host 0.0.0.0 --port 4173
```

**Step 5 — Access from other devices**

Open `http://192.168.1.x:4173` from any device on the same Wi-Fi network.

### PWA Installation

**Desktop (Chrome, Edge):**

1. Open `http://localhost:4173` (after building)
2. Click the install icon (⊕) in the address bar
3. The app installs as a standalone desktop application

**Android (Chrome):**

1. Open `http://192.168.1.x:4173` on your phone
2. Tap the three-dot menu → "Add to Home Screen"
3. The app will install with a home screen icon

**iOS (Safari):**

1. Open the app URL in Safari
2. Tap the Share icon → "Add to Home Screen"

> ⚠ iOS requires HTTPS for full PWA functionality. On a local network, you'd need a tool like `mkcert` to generate a local SSL certificate. Android Chrome works over HTTP on LAN.

### Production Checklist

- [ ] Set a strong `JWT_SECRET` in `.env` (not the default)
- [ ] Run the backend with `--host 0.0.0.0` for network access
- [ ] Build the frontend with `npm run build` (not dev mode)
- [ ] Ensure Ollama is running if chat is needed
- [ ] Verify firewall allows ports 8000 and 4173

---

## 6. WATT-IF Interface

### Navigation

WATT-IF uses a fixed sidebar layout for authenticated pages. The Login and Register pages are shown before authentication. The subsections below follow the chronological order a user experiences the application.

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | User authentication with email and password |
| Register | `/register` | New account creation with email and password |
| Data Entry | `/data-entry` | Upload CSV, manual entry, entry history, model training |
| Dashboard | `/` | Overview with stat cards, anomaly alerts, and forecast chart |
| Forecast | `/forecast` | Generate and view forecasts with horizon selection |
| Ask WATT-IF | `/ask` | AI chat assistant for questions about your data |
| Price Calculator | `/calculator` | Meralco bill breakdown calculator |
| Account Settings | `/account` | Password change, preferences, notifications, data controls |

### 6.1 Login & Registration

These pages are displayed before authentication and are separate from the sidebar navigation.

#### Login Page (`/login`)

The login page presents a centered card with the WATT-IF brand header (logo, title, and "Energy Intelligence" subtitle).

- **Email field** — Required, accepts a valid email address (placeholder: `you@example.com`)
- **Password field** — Required, masked input (placeholder: `••••••••`)
- **Sign In button** — Submits the form; shows "Signing in…" with a disabled state while processing
- **Error display** — An inline alert appears if credentials are invalid (e.g., "Invalid email or password")
- **Rate limiting** — After 10 failed attempts for the same email, login is locked for 15 minutes (HTTP 429)
- **Auto-redirect** — If already authenticated, the page redirects to the Dashboard automatically
- **Register link** — Footer text "Don't have an account?" with a link to `/register`
- **Auto-Login** — If only the default account exists in the system, the app logs in automatically without showing the login form
- **Loading state** — A spinner is displayed while the authentication state is being initialized

#### Register Page (`/register`)

The registration page uses the same centered card layout with the WATT-IF brand header.

- **Email field** — Required, valid email format
- **Password field** — Required, minimum 8 characters. A hint ("Must be at least 8 characters") appears if the entered password is too short
- **Confirm Password field** — Required, must match the password field. A "Passwords do not match" error hint appears in real time if the values differ
- **Create Account button** — Disabled until the password is ≥ 8 characters and both password fields match. Shows "Creating account…" while processing
- **Error display** — Inline alert for registration failures (e.g., email already registered)
- **Auto-redirect** — If already authenticated, the page redirects to the Dashboard
- **Sign In link** — Footer text "Already have an account?" with a link to `/login`
- **Loading state** — A spinner is displayed while the authentication state is being initialized

### 6.2 Data Entry Page

After logging in, the first step for new users is to provide electricity data. This page manages your electricity data and model:

#### Manual Entry
- Select a month (YYYY-MM format)
- Enter kWh consumed
- Optionally override the bill amount or rate
- A **live bill preview** shows the estimated bill (kWh × current rate) as you type
- Exogenous variables (weather, Meralco rate, ENSO, holidays) are auto-resolved

#### CSV Upload
- Click **Choose CSV** and select your file (max 10 MB)
- Minimum required columns: `year_month`, `kwh`, `price`
- Extended schema includes 9 additional exogenous columns for better forecast quality
- After upload, a cleaning report shows: rows received, imputed values, duplicates removed
- Uploaded rows appear in Entry History

#### Entry History
- Paginated table (10 rows per page) showing all entries with resolved exogenous values
- **Edit** — Click edit to change kWh or bill amount inline
- **Delete** — Remove an entry with a confirmation step
- Pagination controls appear when you have more than 10 entries

#### Train Model
- Click **Train Model** to start training on your data
- Requires a minimum of 14 data points (configurable in Settings from 3–60)
- Live status indicator: Idle → Training → Done/Failed
- After training, displays: MAPE (kWh and price), accuracy rating, ARIMA order, training window

#### Clear All Data
- Removes all your bill records, entries, chat history, model, and saved forecasts
- Requires confirmation before proceeding
- After clearing, you'll need to re-upload data and retrain

### 6.3 Dashboard

Once data has been uploaded and a model trained, the dashboard provides an at-a-glance overview of your electricity data:

- **Stat Cards** — Four color-coded cards showing:
  - This Month kWh (blue)
  - Daily Average (teal)
  - Avg Temperature (amber)
  - Avg Humidity (indigo)
- **Anomaly Alert** — An alert card appears if your forecasted consumption exceeds 110% of your historical average
- **Forecast Chart** — Displays the same chart from the Forecast page (shared state)
- **Loading/Empty States** — Shows skeleton placeholders while loading, and an empty state message when no forecast exists

### 6.4 Forecast Page

Generate electricity consumption and cost forecasts:

1. **Select a horizon** — Choose from 1, 3, 6, 9, or 12 months using the horizon selector buttons
2. **View the charts:**
   - **Bar chart** — Forecasted kWh consumption per month with 95% CI error bars
   - **Line chart** — Estimated bill per month with a shaded 95% CI band
3. **Tooltips** — Hover over chart elements to see exact values
4. **Threshold warnings** — If your forecast exceeds your notification thresholds (set in Settings), warning cards appear
5. **Saved forecasts** — Your last generated forecast is persisted and restored when you log back in

> You must train a model before generating forecasts. If no model exists, you'll see a message directing you to the Data Entry page.

### 6.5 Ask WATT-IF (Chat Assistant)

Ask natural-language questions about your electricity usage and forecasts:

- Type a question (1–500 characters) and press Enter or click Send
- The assistant streams its response in real time using SSE
- Answers are grounded in your actual forecast data and historical EDA summaries
- Chat history is persisted per user (up to 100 messages, configurable)

**Example questions:**
- "What will my bill be next month?"
- "Which month has the highest forecast?"
- "Why is my bill higher in April?"
- "How does El Niño affect my electricity usage?"
- "What's my average monthly consumption?"

**Clear Chat** — Wipes the entire conversation from both UI and database.

> Requires Ollama to be running with `qwen3:1.7b` loaded. If Ollama is down, you'll see a graceful error message.

### 6.6 Price Calculator

Calculate your Meralco bill breakdown based on consumption:

1. **Enter kWh** — Type your monthly consumption
2. **Select customer type** — Residential, General Service A, or General Service B (pre-filled from Settings)
3. **View breakdown** — Full charge-by-charge breakdown:
   - Generation Charge
   - Transmission Charge
   - System Loss Charge
   - Distribution Charge
   - Supply Charge
   - Metering Charge
   - Other Charges (Lifeline, ICERA, Feed-in Tariff, etc.)
4. **Auto bracket selection** — The correct consumption bracket is automatically selected based on your kWh input
5. **Manual override** — You can manually select a different bracket if needed
6. **Refresh rates** — Force-refresh the cached Meralco rate (normally refreshed every 24 hours)

### 6.7 Account Settings

#### Password Management
- Change your password (requires current password + new password ≥ 8 characters + confirmation)

#### Preferences
- **Customer Type** — Residential, General Service A, or General Service B
- **Default Forecast Horizon** — 1, 3, 6, 9, or 12 months (pre-selects on Forecast page)
- **Electricity Rate Override** — Manual ₱/kWh rate that bypasses the live Meralco scraper

#### Chat Preferences
- **Max Message History** — 10 to 500 messages retained
- **Auto-Clear on Logout** — Wipe chat history when you log out

#### Notification Thresholds
- **Monthly kWh Budget** — Alert when forecast exceeds this (0–99,999)
- **Bill Ceiling** — Alert when estimated bill exceeds this amount (0–₱999,999)
- **High Consumption Warning** — Alert threshold in kWh (0–99,999)

#### Model Retraining
- **Auto-Retrain on Upload** — Toggle automatic retraining when a CSV is uploaded
- **Minimum Data Points** — Set the minimum rows required before training (3–60)

#### Data & Privacy
- **Clear Chat History** — Delete all chat messages (with confirmation)
- **Clear All Data** — Wipe everything and reset (with confirmation)

---

## 7. Accessibility Features

### Keyboard Navigation
- Full keyboard navigability across all pages and interactive elements
- **Focus trap** in mobile drawer menu — Tab key cycles within the open drawer
- **Escape key** closes the mobile drawer
- Sidebar navigation items are keyboard-focusable

### Screen Reader Support
- Semantic HTML structure with proper heading hierarchy
- ARIA labels on interactive elements (buttons, inputs, navigation)
- Form inputs have associated labels
- Chart descriptions provide text alternatives

### Visual Accessibility
- **Dark/Light mode** — Toggle available for users who prefer different contrast levels
- **Design token system** — Consistent color contrast ratios across themes
- **Color-coded stat cards** use distinct hues (blue, teal, amber, indigo) to aid differentiation
- Charts use both color and shape (bars vs. lines, error bars) to convey information

### Motion & Layout
- No auto-playing animations or carousels
- Fixed sidebar layout prevents content shift during navigation
- Loading states use skeleton placeholders (no flashing elements)
- Responsive layout adapts from 360px mobile to full desktop

### PWA Accessibility
- Installable as a standalone app (avoids browser chrome clutter)
- Offline banner clearly communicates connectivity status
- Health indicator shows subsystem status visually

---

## 8. Existing Bugs and How to Resolve

### Module Import Error on Backend Startup

If the user encounters a `ModuleNotFoundError` when starting the backend server, they should first verify that all Python dependencies have been installed correctly. The user must ensure they are running the command from the project root directory (the folder containing `api/`, `model/`, `pipeline/`, etc.) and not from within a subdirectory. If using a virtual environment, it must be activated before running the server. Once the environment is properly configured with `pip install -r requirements.txt`, the backend can be started successfully using `python -m uvicorn api.main:app --reload --port 8000`.

### Model Not Trained Error

If the user attempts to generate a forecast and receives a "Model not trained" error (HTTP 503), this means no SARIMAX model artifact exists for their account. The user must first navigate to the Data Entry page, upload a CSV file or manually enter at least 14 months of electricity data, and then click the Train Model button. Once the training status shows "Done," the user can return to the Forecast page and generate predictions without issue.

### LLM Service Unavailable

If the user sends a question in the Ask WATT-IF chat and receives an "LLM service unavailable" error, this indicates that Ollama is not running or the required language model has not been downloaded. The user should verify that Ollama is installed and running as a background service, and that the `qwen3:1.7b` model has been pulled using `ollama pull qwen3:1.7b`. Once Ollama is active and the model is loaded, the chat assistant will respond normally.

### CORS Error or Blank Page on Frontend

If the user sees CORS errors in the browser console or the frontend renders as a blank white page, this typically means the backend server is not running or was started after the frontend attempted to connect. The user should ensure the backend is started first, then start the frontend development server. If the issue persists, restarting both terminals usually resolves it. The user should also verify that their firewall is not blocking port 8000.

### Too Many Login Attempts

If the user receives a "too many attempts" error when trying to log in, this means the rate limiter has been triggered after 10 failed login attempts within a 15-minute window for the same email address. The user should wait 15 minutes for the rate limiter to reset automatically, or restart the backend server to clear the in-memory rate limiter. They should also verify that they are entering the correct credentials before attempting to log in again.

### Flat or Inaccurate Forecasts

If the user notices that their forecast line appears flat or does not reflect expected seasonal consumption patterns, this is typically caused by insufficient or low-quality training data. The user should ensure they have at least 24 months of historical data to allow the model to capture seasonal trends. Including exogenous variables (temperature, rainfall, El Niño status) in the CSV significantly improves forecast accuracy. A synthetic dataset is available at `data/synthetic_2022_2025.csv` for testing purposes.

### Ollama Warmup Timeout on First Chat

If the user's first chat question takes an unusually long time (60+ seconds) or times out, this occurs because Ollama needs to load the language model into memory on the first request after startup. The backend sends a warmup request on initialization, so the user should wait approximately 30 seconds after starting the backend before using the chat feature. If a timeout occurs, simply retrying the question will work as the model remains in memory for subsequent requests.

---

## Appendix A — Quick Reference

### Default Account Credentials

| Field | Value |
|-------|-------|
| Email | `wattif@gmail.com` |
| Password | `wattif` |

### CSV Minimum Schema

```csv
year_month,kwh,price
2023-01,342.5,4210.50
2023-02,310.0,3890.00
```

### Useful Commands

| Action | Command |
|--------|---------|
| Start backend | `python -m uvicorn api.main:app --reload --port 8000` |
| Start frontend (dev) | `cd frontend && npm run dev` |
| Build frontend | `cd frontend && npm run build` |
| Preview built frontend | `cd frontend && npm run preview` |
| Pull Ollama model | `ollama pull qwen3:1.7b` |
| Run backend tests | `python -m pytest tests/ -q` |
| Run frontend tests | `cd frontend && npm test` |
| Generate synthetic data | `python data/generate_synthetic_2022_2025.py` |

### API Health Check

Visit `http://localhost:8000/health` to check the status of all subsystems:
- Data Pipeline
- SARIMAX Model
- Vector Store (ChromaDB)
- LLM Service (Ollama)

### Interactive API Docs

Visit `http://localhost:8000/docs` for the Swagger UI with all available endpoints.
