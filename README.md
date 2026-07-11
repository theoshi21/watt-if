# WATT-IF

A locally-hosted Progressive Web App for forecasting household electricity consumption and cost in the Philippines.

Upload your monthly electricity bill history as a CSV or enter readings manually, get SARIMAX-powered forecasts for the next 1, 3, 6, 9, or 12 months, ask natural-language questions about your energy usage, and calculate your exact Meralco bill breakdown — all running on your own machine with no cloud dependency.

**Stack:** FastAPI · pmdarima · ChromaDB · SQLite · Ollama (Qwen3 1.7B) · React · Vite · Recharts · sentence-transformers · vite-plugin-pwa

---

## Features

### Forecasting
- **SARIMAX forecasting** — trains on your bill history with 9 exogenous variables: temperature, rainfall, humidity, Meralco rate, holidays, hot days, rainy days, El Niño status, and weekend count
- **Extended horizons** — forecast 1, 3, 6, 9, or 12 months ahead
- **95% confidence intervals** — every forecast shows CI bands on the chart
- **Bar chart for consumption** — kWh forecast shown as a bar chart with error bars; bill forecast shown as a line chart
- **Month-aware fallback exog** — when no future exogenous values are provided, the model estimates using same-calendar-month historical averages and Philippine climate priors (never all-zero inputs)
- **Correct forecast anchoring** — forecasts always project forward from your most recent data point, not from the training split cutoff
- **Saved forecasts** — generated forecasts are persisted per user and restored on login

### Data Entry & Management
- **Manual entry** — enter a month and kWh reading; rate, weather, and ENSO are auto-resolved from live APIs
- **Live bill preview** — estimated bill (kWh × live Meralco rate) shown as you type
- **CSV upload** — upload historical data in bulk; all uploaded rows appear in Entry History
- **Entry History** — paginated table (10 rows/page) showing all entries with auto-resolved exogenous values
- **Inline edit/delete** — edit kWh and bill amount or delete entries directly in the history table
- **Manual Train Model** — training only runs when you click the Train Model button, not automatically on every entry
- **Clear All Data** — wipe all training data and the model artefact with a confirmation step

### RAG Chat Assistant
- **Natural-language questions** — ask about your forecast in plain English; answers grounded in retrieved forecast data and historical EDA summaries
- **Full-horizon context** — the assistant uses whichever forecast you last generated (1m through 12m), not just the default 3-month view
- **Clear chat** — wipes conversation from both the UI and the database
- **Plain conversational answers** — no headers, no emoji, no structured reports

### Price Calculator
- **Live Meralco rate** — fetches the current Summary Schedule of Rates; cached for 24 hours
- **Full bill breakdown** — generation, transmission, system loss, distribution, supply, metering, and other charges per bracket
- **Auto bracket selection** — automatically picks the right consumption bracket based on your kWh; manual override available
- **Residential and General Service** — supports multiple customer types

### Account System & Security
- **User registration** — email + password, validated with min 8 chars and proper email format
- **JWT authentication** — 24-hour token expiry, bcrypt password hashing (cost 12)
- **Login rate limiting** — max 10 failed attempts per email within a 15-minute window (HTTP 429)
- **Timing-attack mitigation** — dummy bcrypt check on non-existent emails
- **Default account** — auto-seeded `wattif@gmail.com` / `wattif` for first-time use
- **Auto-login** — if no additional accounts exist, logs in with the default account automatically
- **Change password** — requires current password confirmation
- **Per-user data isolation** — all data (bills, entries, forecasts, chat history, models) is scoped to the authenticated user
- **Auth guard** — all app pages redirect to login if unauthenticated

### Settings
- **Customer type** — Residential, General Service A, or General Service B; pre-selects in the Price Calculator
- **Default forecast horizon** — 1, 3, 6, 9, or 12 months; pre-selects on the Forecast page
- **Electricity rate override** — manual ₱/kWh rate that bypasses the live Meralco scraper
- **Chat preferences** — max message history (10–500) and auto-clear chat on logout
- **Notification thresholds** — monthly kWh budget, bill ceiling (₱), and high consumption warning; triggers alerts on the Forecast page when exceeded
- **Model retraining** — auto-retrain on CSV upload toggle and configurable minimum data points before training (3–60)
- **Data & privacy** — clear chat history and clear all data with confirmation steps
- **Input boundaries** — all numeric inputs enforce max limits to prevent overflow (kWh: 99,999; bill: ₱999,999; rate: ₱100/kWh)

### UI & App Shell
- **Multi-page layout** — sidebar navigation with Dashboard, Forecast, Ask WATT-IF, Price Calculator, Data Entry, and Account Settings routes
- **Fixed sidebar** — always visible, never scrolls, fits the full viewport without overflow
- **Dark / light mode** — toggle persisted to `localStorage`
- **Color-coded stat cards** — dashboard cards have accent colors and icons (blue kWh, teal daily avg, amber temp, indigo humidity)
- **Anomaly detection** — alerts when forecasted consumption is significantly above your average
- **Design token system** — all colors, fonts (Inter, Space Mono), and spacing use CSS custom properties; consistent across light and dark themes
- **Offline-capable PWA** — installable as a desktop app; shows cached forecast data when offline
- **Health check** — `/health` reports status of all four subsystems

### Backend & Data
- **Live Meralco rate scraper** — fetches current residential rates by bracket
- **Open-Meteo weather integration** — real historical and forecast weather for Metro Manila
- **NOAA ENSO lookup** — El Niño / La Niña phase from the ONI index
- **Model evaluation panel** — shows MAPE breakdown (kWh, price, average), accuracy rating, ARIMA order, and training window
- **Synthetic dataset generator** — `data/generate_synthetic_2022_2025.py` produces a realistic 48-month Philippine household dataset (2022–2025) with real Meralco rate anchors, El Niño 2023, and La Niña 2022/2025
- **Per-user model storage** — each user's trained SARIMAX artefact is stored in `data/models/<user_id>/`

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | |
| Node.js | 18+ | |
| npm | 9+ | Comes with Node |
| Ollama | Latest | For the RAG chat feature only |

---

## 1. Clone / open the project

```
cd C:\Users\<you>\OneDrive\Desktop\WATT-IF
```

---

## 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Tip:** Use a virtual environment:
> ```bash
> python -m venv .venv
> .venv\Scripts\activate   # Windows
> pip install -r requirements.txt
> ```

---

## 3. Environment variables

Copy `.env.example` to `.env` and set your JWT secret:

```
JWT_SECRET=your-strong-random-secret-here
```

If not set, the app defaults to `dev-secret-change-in-production` (fine for local development).

---

## 4. Install Ollama

Ollama runs the Qwen3 1.7B language model locally for the RAG chat feature.

1. Download from **https://ollama.com/download/windows**
2. Run `OllamaSetup.exe` — installs silently and adds `ollama` to PATH
3. Open a new terminal and pull the model:

```bash
ollama pull qwen3:1.7b
```

Ollama starts as a background service automatically after install.

> Upload, forecast, and all data features work without Ollama. Only `/ask` (chat) requires it.

---

## 5. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## 6. Run the application

You need **two terminals** running simultaneously.

### Terminal 1 — Backend (FastAPI)

From the project root:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

> **Important:** Run from the project root — the folder containing `api/`, `model/`, `pipeline/`, etc.

API available at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### Terminal 2 — Frontend (React PWA)

From the `frontend/` directory:

```bash
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 7. Use the app

### Step 1 — Log in

On first launch, the app auto-logs in with the default account (`wattif@gmail.com` / `wattif`). If you've registered additional accounts, you'll see the login page instead.

- **Register** a new account from the login page
- **Change password** via the Account Settings page in the sidebar

### Step 2 — Add your bill data

**Option A — Upload a CSV**

Click **Choose CSV** on the Data Entry page. The minimum required columns are:

```
year_month,kwh,price
2023-01,342.5,4210.50
2023-02,310.0,3890.00
```

The extended schema (recommended for best forecast quality):

```
year_month,kwh,price,meralco_rate,avg_temperature,avg_humidity,
total_rainfall_mm,holiday_count,weekend_count,hot_days_count,
rainy_days_count,is_el_nino
```

| Column | Format | Description |
|---|---|---|
| `year_month` | `YYYY-MM` | The billing month |
| `kwh` | Number | Total electricity consumed (kWh) |
| `price` | Number | Total bill amount in PHP |
| `meralco_rate` | Number | Meralco rate in ₱/kWh |
| `avg_temperature` | Number | Average monthly temperature in °C |
| `avg_humidity` | Number | Average monthly humidity in % |
| `total_rainfall_mm` | Number | Total monthly rainfall in mm |
| `holiday_count` | Integer | Number of public holidays in the month |
| `weekend_count` | Integer | Number of weekend days in the month |
| `hot_days_count` | Integer | Number of days with temperature ≥ 33°C |
| `rainy_days_count` | Integer | Number of rainy days in the month |
| `is_el_nino` | 0 or 1 | Whether El Niño was active that month |

A synthetic test dataset covering 2022–2025 (48 months) is available at `data/synthetic_2022_2025.csv`. It includes realistic Meralco rates, El Niño 2023, and La Niña conditions.

**Option B — Manual entry**

On the Data Entry page, enter a month and kWh reading. The system auto-resolves:
- Meralco rate (live scrape or DB fallback)
- Weather data (Open-Meteo API)
- ENSO phase (NOAA ONI index)
- Weekend count (real calendar)

A live bill estimate (kWh × current rate) is shown as you type.

**Minimum data:** 14 rows to train the model. 2–3 years (24–36 rows) gives the best forecast quality.

### Step 3 — Train the model

After adding data, click **Train Model** on the Data Entry page. Training takes ~60 seconds. The panel shows live status (Idle → Training → Done/Failed) and displays the trained model's MAPE, accuracy rating, and training window once complete.

### Step 4 — Generate a forecast

Go to the **Forecast** page. Select **1m**, **3m**, **6m**, **9m**, or **12m** to generate a forecast. The charts show:
- Bar chart: forecasted kWh consumption with 95% CI error bars per month
- Line chart: estimated bill per month with 95% CI band

If your forecast detects anomalies (consumption significantly above average), an alert card appears on the Dashboard.

### Step 5 — Ask questions (requires Ollama)

Go to **Ask WATT-IF**. Type a natural-language question. The assistant answers using the retrieved forecast data and historical analysis.

**Examples:**
- *"What will my bill be next month?"*
- *"Which month has the highest forecast?"*
- *"Why is my bill higher in April?"*
- *"How does El Niño affect my electricity usage?"*

Click **Clear chat** to wipe the conversation and start fresh (also clears the database history).

### Step 6 — Calculate your bill

Go to **Price Calculator**. Enter your monthly consumption in kWh and select your account type. The calculator shows the full Meralco bill breakdown by charge component (generation, transmission, system loss, distribution, supply, metering, and other charges) for the current rate schedule.

---

## 8. Generate a synthetic dataset (optional)

To generate a realistic 48-month dataset for testing:

```bash
python data/generate_synthetic_2022_2025.py
```

This produces `data/synthetic_2022_2025.csv` with:
- Jan 2022 – Dec 2025 (48 months)
- Meralco rates anchored to real published figures (₱9.74 → ₱12.55/kWh)
- El Niño Jun 2023 – Mar 2024 (+10% kWh, hotter/drier)
- La Niña 2022 and 2025 (cooler/wetter)
- Philippine seasonal pattern (peak Apr–May, trough Jul–Sep)

---

## 9. Regenerate EDA summaries (optional)

After uploading new data, EDA summaries are regenerated during retraining. To regenerate manually:

```bash
python data/eda.py          # generates data/eda_summaries.json
python data/ingest_eda.py   # ingests summaries into ChromaDB
```

---

## 10. Install as a PWA (optional)

### On the same machine

```bash
# In the frontend/ directory
npm run build
npm run preview
```

Open **http://localhost:4173**. Click the install icon in the browser address bar to install as a standalone desktop app.

### On a phone (same Wi-Fi network)

This lets you install WATT-IF on your phone while the backend runs on your PC.

**Step 1 — Find your PC's local IP**

Run in PowerShell:
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch '^(127\.|169\.)' } | Select-Object IPAddress
```
You'll get something like `192.168.1.x`.

**Step 2 — Create `frontend/.env.local`**

```
VITE_API_BASE=http://192.168.1.x:8000
```

Replace `192.168.1.x` with your actual IP.

**Step 3 — Start the backend on the network**

```bash
# From project root
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Step 4 — Build and serve the frontend**

```bash
# From frontend/
npm run build
npm run preview -- --host 0.0.0.0 --port 4173
```

**Step 5 — Open on your phone**

Make sure your phone is on the same Wi-Fi. Open `http://192.168.1.x:4173` in your browser.

- **Android (Chrome):** tap the three-dot menu → "Add to Home Screen"
- **iOS (Safari):** tap the Share icon → "Add to Home Screen"

> **Note:** iOS Safari requires HTTPS for PWA install. On Android Chrome, HTTP over a local network works fine. If you need iOS support, you'd need to set up a local SSL certificate with a tool like `mkcert`.

---

## Project structure

```
WATT-IF/
├── api/
│   ├── main.py                  # FastAPI app — all endpoints
│   ├── auth.py                  # Auth endpoints (register, login, change-password)
│   ├── dependencies.py          # JWT validation dependency (get_current_user)
│   ├── rate_limiter.py          # In-memory login rate limiter (10 attempts / 15 min)
│   └── schemas.py               # Pydantic request/response models
├── pipeline/
│   ├── data_pipeline.py         # CSV ingestion, cleaning, SQLite persistence
│   ├── feature_engineering.py   # Month-aware seasonality exog estimation
│   └── models.py                # Shared dataclasses (MonthlyRecord, ForecastMonth, etc.)
├── model/
│   ├── sarimax_model.py         # SARIMAX training, forecasting, fallback exog
│   └── retraining.py            # Retraining pipeline + EDA ingestion
├── storage/
│   ├── db.py                    # SQLite schema (monthly_bill_records, data_entry_log,
│   │                            #   chat_history, training_log, users, saved_forecasts,
│   │                            #   user_settings)
│   ├── vector_store.py          # ChromaDB forecast document store
│   └── eda_store.py             # ChromaDB EDA summary store
├── rag/
│   └── rag_service.py           # RAG orchestration — retrieval + Ollama streaming
├── scraper/
│   ├── meralco_rate.py          # Live Meralco residential rate scraper (cached 24h)
│   ├── weather.py               # Open-Meteo monthly weather fetcher
│   └── enso.py                  # NOAA ONI ENSO phase lookup
├── data/
│   ├── eda.py                   # EDA script — generates relationship summaries
│   ├── ingest_eda.py            # Ingests eda_summaries.json into ChromaDB
│   ├── generate_dataset.py      # Original synthetic dataset generator (2020–2024)
│   ├── generate_synthetic_2022_2025.py  # Realistic PH synthetic dataset (2022–2025)
│   ├── synthetic_2022_2025.csv  # Generated 48-month dataset
│   ├── models/                  # Per-user trained model artefacts (data/models/<user_id>/)
│   ├── monthly_bills.csv        # Simple dataset (year_month, kwh, price only)
│   └── test_bills.csv           # Minimal test dataset
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # Entry point — BrowserRouter + AuthProvider + ThemeProvider + ForecastProvider
│   │   ├── App.tsx              # Route table (public: login/register, protected: all others)
│   │   ├── api/
│   │   │   ├── client.ts        # Typed API client (all endpoints)
│   │   │   └── types.ts         # TypeScript interfaces mirroring Pydantic schemas
│   │   ├── components/
│   │   │   ├── AppShell.tsx     # Layout shell with sidebar + topbar + focus trap
│   │   │   ├── AuthGuard.tsx    # Redirects to /login if not authenticated
│   │   │   ├── Sidebar.tsx      # Fixed sidebar navigation
│   │   │   ├── TopBar.tsx       # Page title + dark mode toggle + nav controls
│   │   │   ├── ChatPanel.tsx    # Streaming chat UI with persistent history
│   │   │   ├── ForecastChart.tsx # Bar chart (kWh) + line chart (bill) with CI
│   │   │   ├── StatCard.tsx     # Color-coded stat card with icon
│   │   │   ├── TrainModelPanel.tsx # Manual train button + status + model info
│   │   │   ├── UploadPanel.tsx  # CSV upload (no auto-train)
│   │   │   ├── HorizonSelector.tsx # 1/3/6/9/12m selector
│   │   │   ├── ModelEvaluation.tsx # MAPE, order, training window display
│   │   │   ├── HealthIndicator.tsx # Subsystem status dots
│   │   │   ├── ModelStatusPill.tsx # Model active/trained status
│   │   │   ├── AnomalyCard.tsx  # Anomaly alert banner (SVG icon, no emoji)
│   │   │   ├── DarkModeToggle.tsx
│   │   │   └── OfflineBanner.tsx
│   │   ├── context/
│   │   │   ├── AuthContext.tsx    # JWT auth state, login/logout/register
│   │   │   ├── ForecastContext.tsx # Shared forecast state
│   │   │   └── ThemeContext.tsx    # Dark/light theme state
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx       # Email + password login form
│   │   │   ├── RegisterPage.tsx    # New account registration form
│   │   │   ├── AccountSettingsPage.tsx # User settings (password, preferences, notifications)
│   │   │   ├── DashboardPage.tsx   # Stat cards + anomaly + chart
│   │   │   ├── ForecastPage.tsx    # Horizon selector + forecast charts
│   │   │   ├── AskPage.tsx         # Full-height chat panel
│   │   │   ├── DataEntryPage.tsx   # Manual entry + upload + train + history
│   │   │   └── PriceCalculatorPage.tsx # Meralco bill calculator
│   │   ├── styles/
│   │   │   ├── tokens.css       # CSS custom properties (light + dark themes)
│   │   │   └── index.css        # Global reset, .card, .btn-*, layout classes
│   │   └── test/                # Vitest unit and property-based tests
│   └── package.json
├── tests/                       # pytest test suites
│   ├── api/                     # test_api.py, test_auth.py
│   ├── model/                   # test_sarimax_model.py, test_retraining.py
│   ├── pipeline/                # test_data_pipeline.py
│   ├── rag/                     # test_rag_service.py
│   ├── storage/                 # test_vector_store.py
│   └── integration/             # test_integration.py
├── Documentation/               # Test case documentation (TC_*.md)
├── design/                      # UI mockups (Mobile UI.png, Web UI.png)
├── .env.example                 # Environment variable template
└── requirements.txt
```

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create a new user account |
| `POST` | `/auth/login` | Authenticate and receive a JWT |
| `POST` | `/auth/change-password` | Update the current user's password |
| `GET` | `/auth/has-users` | Check if additional accounts exist (for auto-login) |
| `POST` | `/upload` | Ingest a CSV bill dataset |
| `POST` | `/forecast` | Generate SARIMAX forecast (horizon 1/3/6/9/12) |
| `GET` | `/saved-forecast` | Load the user's persisted forecast |
| `POST` | `/saved-forecast` | Save the current forecast for the user |
| `POST` | `/ask` | Streaming RAG answer (SSE) |
| `POST` | `/retrain` | Manually trigger full model retrain |
| `GET` | `/status` | Background training state (idle/running/done/failed) |
| `GET` | `/model-info` | MAPE, order, training window, accuracy rating |
| `GET` | `/health` | Subsystem health check |
| `GET` | `/data-entries` | All entry history rows for the authenticated user |
| `POST` | `/data-entries` | Create a manual entry |
| `PUT` | `/data-entries/{id}` | Update kWh or bill amount |
| `DELETE` | `/data-entries/{id}` | Delete one entry |
| `DELETE` | `/data/all` | Wipe all user data and model artefact |
| `GET` | `/chat-history` | Last 100 chat messages |
| `POST` | `/chat-history` | Persist a chat message |
| `DELETE` | `/chat-history` | Clear all chat history |
| `GET` | `/meralco-rate` | Current Meralco rate schedule (cached 24h) |
| `POST` | `/meralco-rate/refresh` | Force-refresh Meralco rate |
| `GET` | `/settings` | Retrieve user preferences |
| `PUT` | `/settings` | Update user preferences (partial) |

> All endpoints except `/auth/*`, `/meralco-rate`, and `/health` require a valid JWT in the `Authorization: Bearer <token>` header.

---

## Running the tests

### Backend (pytest)

```bash
# From project root
python -m pytest tests/ -q
```

### Frontend (vitest)

```bash
# From frontend/
npm test
```

---

## Troubleshooting

**`ModuleNotFoundError` on startup**  
Run `pip install -r requirements.txt` and ensure your virtual environment is activated. Always start uvicorn from the project root.

**`SARIMAX artefact not found` / forecast returns 503**  
Upload data first, then click **Train Model** on the Data Entry page. Check `/status` to see if training is still running.

**Forecast months start from 2024 instead of the current date**  
This was caused by the training window using the 80% split end instead of the full dataset end. Fixed — re-train after uploading your latest data.

**Chat returns "LLM service unavailable"**  
Ollama is not running. Start it with `ollama serve` or verify it is running as a background service. Pull the model with `ollama pull qwen3:1.7b`.

**Chat answer uses headers, bullet lists, or emoji**  
Restart the backend to reload the updated system prompt which enforces plain conversational output.

**Delete or Edit buttons do nothing**  
This was a CORS issue — `DELETE` and `PUT` were missing from the allowed methods. Fixed — restart the backend.

**Bill column shows `—` after manual entry**  
The backend now backfills `bill_amount` with the computed price (kWh × resolved Meralco rate). Restart the backend and re-submit the entry.

**CSV upload rows not appearing in Entry History**  
CSV rows are now mirrored to `data_entry_log` after a successful upload. Re-upload your CSV after restarting the backend.

**Frontend shows blank page or CORS error**  
Ensure the backend is running on port 8000 before opening the frontend. The backend auto-detects your LAN IP for CORS.

**Forecast looks flat or inaccurate**  
Use at least 24 months of data spanning more than one calendar year. Including exogenous columns (temperature, rainfall, El Niño) significantly improves accuracy.

**"Too many login attempts" (HTTP 429)**  
The rate limiter blocks after 10 failed login attempts per email. Wait 15 minutes or restart the backend to reset.
