# ⚡ WATT-IF

A locally-hosted Progressive Web App for forecasting household electricity consumption and cost in the Philippines.

Upload your monthly electricity bill history as a CSV, get SARIMAX-powered forecasts for the next 1, 3, or 6 months, and ask natural-language questions about your energy usage — all running on your own machine with no cloud dependency.

**Stack:** FastAPI · pmdarima · ChromaDB · SQLite · Ollama (Qwen3 1.7B) · React · Vite · Recharts · sentence-transformers · vite-plugin-pwa

---

## Features

- **SARIMAX forecasting** — trains on your historical bill data with 9 exogenous variables (temperature, rainfall, humidity, Meralco rate, holidays, hot days, rainy days, El Niño status, weekend count)
- **Month-aware fallback exog** — when no explicit future exogenous values are provided, the model estimates realistic per-month values using same-calendar-month historical averages and Philippine climate priors, so forecasts are never driven by all-zero inputs
- **RAG chat assistant** — ask plain-language questions about your forecast; answers are grounded in retrieved forecast documents and historical EDA summaries
- **Data-grounded explanations** — for "why" and "how" questions the assistant explains in simple terms (e.g. "It's hotter this month, so more aircon use") using real data, not templates
- **Automatic retraining** — the model retrains in the background whenever you upload a new CSV with additional months
- **EDA vector store** — historical analysis summaries (seasonality, temperature/rainfall/El Niño correlations, Meralco rate trends) are embedded and retrieved alongside forecast data for richer answers
- **Forecast confidence intervals** — every forecast month includes a 95% CI band shown on the chart
- **Model evaluation panel** — shows MAPE, ARIMA order, seasonal order, and training window
- **Offline-capable PWA** — installable as a desktop app; shows cached forecast data when offline
- **Health check endpoint** — `/health` reports the status of all four subsystems

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

## 3. Install Ollama

Ollama runs the Qwen3 1.7B language model locally for the RAG chat feature.

1. Download from **https://ollama.com/download/windows**
2. Run `OllamaSetup.exe` — installs silently and adds `ollama` to PATH
3. Open a new terminal and pull the model:

```bash
ollama pull qwen3:1.7b
```

Ollama starts as a background service automatically after install.

> The `/upload` and `/forecast` endpoints work without Ollama. Only `/ask` (chat) requires it.

---

## 4. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## 5. Run the application

You need **two terminals** running simultaneously.

### Terminal 1 — Backend (FastAPI)

From the project root:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

> **Important:** Run from the project root — the folder containing `api/`, `model/`, `pipeline/`, etc. Running from a subfolder causes `ModuleNotFoundError: No module named 'api'`.

API available at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### Terminal 2 — Frontend (React PWA)

From the `frontend/` directory:

```bash
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 6. Use the app

### Step 1 — Upload your bill data

Click **"Choose CSV"** and select a monthly electricity bill CSV. The minimum required columns are:

```
year_month,kwh,price
2023-01,342.5,4210.50
2023-02,310.0,3890.00
```

The extended schema (recommended for best forecast quality) includes exogenous variables:

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

- Minimum **14 rows** required to train the model
- 2–3 years of history (24–36 rows) gives the best forecast quality
- Missing optional columns are filled with defaults automatically
- A synthetic test file is provided at `data/test_bills.csv`
- The full extended dataset used in development is at `data/monthly_bills.csv`

After upload, model retraining starts automatically in the background. A status indicator shows when training is complete.

### Step 2 — Generate a forecast

Select **1m**, **3m**, or **6m** to generate a forecast for the next 1, 3, or 6 months. The chart shows:
- Forecasted kWh consumption and estimated bill per month
- 95% confidence interval shaded bands
- Exact values on hover

When no explicit exogenous values are provided, the system estimates them using:
- Same-calendar-month historical averages (e.g. July forecast uses all historical July records)
- Recent Meralco rate trend (6-month linear projection)
- Real calendar weekend count for each future month
- Philippine PAGASA climate priors as a fallback when no historical data exists for a month

### Step 3 — Ask questions (requires Ollama)

Type a natural-language question in the chat panel. The assistant answers using only the retrieved forecast data and historical analysis — it never invents numbers.

**Factual questions** get direct answers:
- *"What will my bill be in March?"*
- *"Which month has the highest forecast?"*
- *"How much will I use in the next 3 months?"*

**Explanatory questions** get plain-language explanations based on the actual forecast drivers:
- *"Why is my bill higher this month?"*
- *"How does El Niño affect my electricity usage?"*
- *"Why did the forecast increase?"*
- *"What affects my electricity bill the most?"*
- *"Why is March more expensive than February?"*

The chat assistant:
- Only explains when you ask why/how — simple factual questions get short direct answers
- Uses everyday language ("It's hotter this month, so more aircon use") rather than technical jargon
- Compares against historical patterns when relevant (e.g. "Historically, this month tends to be one of the higher ones")
- States clearly when the available data is insufficient to explain something

---

## 7. Regenerate EDA summaries (optional)

After uploading new data, EDA summaries are automatically regenerated and ingested during retraining. To regenerate them manually:

```bash
# From project root
python data/eda.py          # generates data/eda_summaries.json
python data/ingest_eda.py   # ingests summaries into ChromaDB
```

The EDA summaries cover: dataset overview, annual summaries, year-over-year changes, monthly seasonality, long-term trends, Meralco rate trends, highest/lowest consumption months, temperature vs kWh, rainfall vs kWh, holiday effects, El Niño effects, quarterly patterns, humidity vs kWh, hot days vs kWh, and a bill driver ranking.

---

## 8. Install as a PWA (optional)

For the full offline experience, run a production build:

```bash
# In the frontend/ directory
npm run build
npm run preview
```

Open **http://localhost:4173**. An install icon appears in the browser address bar — click it to install WATT-IF as a standalone desktop app. When offline, the app shows the most recently cached forecast.

---

## Project structure

```
WATT-IF/
├── api/
│   ├── main.py                  # FastAPI app — /upload, /forecast, /ask, /health, /model-info
│   └── schemas.py               # Pydantic request/response models
├── pipeline/
│   ├── data_pipeline.py         # CSV ingestion, cleaning, SQLite persistence
│   ├── feature_engineering.py   # Month-aware seasonality exog estimation
│   └── models.py                # Shared dataclasses (MonthlyRecord, ForecastMonth, etc.)
├── model/
│   ├── sarimax_model.py         # SARIMAX training, forecasting, month-aware fallback exog
│   └── retraining.py            # Automatic retraining pipeline + EDA ingestion
├── storage/
│   ├── db.py                    # SQLite schema and connection helpers
│   ├── vector_store.py          # ChromaDB forecast document store (sentence-transformers)
│   └── eda_store.py             # ChromaDB EDA summary store
├── rag/
│   └── rag_service.py           # RAG orchestration — retrieval + Ollama streaming
├── data/
│   ├── eda.py                   # EDA script — generates relationship-oriented summaries
│   ├── ingest_eda.py            # Ingests eda_summaries.json into ChromaDB
│   ├── generate_dataset.py      # Synthetic dataset generator
│   ├── monthly_bills.csv        # Full extended dataset (2020–2024, 60 months)
│   └── test_bills.csv           # Minimal test dataset
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root component and layout
│   │   ├── api/                 # Typed API client + TypeScript types
│   │   └── components/
│   │       ├── ChatPanel.tsx    # Streaming chat UI with auto-scroll
│   │       ├── ForecastChart.tsx
│   │       ├── UploadPanel.tsx
│   │       ├── HorizonSelector.tsx
│   │       ├── ModelEvaluation.tsx
│   │       ├── HealthIndicator.tsx
│   │       └── OfflineBanner.tsx
│   ├── vite.config.ts           # Vite + PWA configuration
│   └── package.json
├── tests/                       # pytest + vitest test suites
└── requirements.txt
```

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

## Health check

With the backend running, visit `http://localhost:8000/health`:

```json
{
  "status": "ok",
  "subsystems": {
    "data_pipeline": "operational",
    "sarimax_model": "operational",
    "vector_store": "operational",
    "llm_service": "operational"
  },
  "model_trained_at": "2025-06-21T10:30:00+00:00",
  "last_upload_at": "2025-06-21T10:29:45+00:00"
}
```

`llm_service` shows `"degraded"` if Ollama is not running — upload, forecast, and health all still work normally.

---

## Troubleshooting

**`ModuleNotFoundError` on startup**  
Run `pip install -r requirements.txt` and make sure your virtual environment is activated. Always start uvicorn from the project root.

**`SARIMAX artefact not found` on /forecast**  
Upload a CSV first. The model trains automatically after a successful upload. Check `/status` to see if training is still running.

**Forecast shows 0.0 kWh for all months**  
This was a known issue where the fallback exogenous values defaulted to all zeros. It is fixed — the model now uses month-aware historical seasonality and Philippine climate priors. Re-upload your CSV to retrain with the fix applied.

**Chat returns "LLM service unavailable"**  
Ollama is not running. Start it with `ollama serve` or check that it is running as a background service. Make sure `qwen3:1.7b` has been pulled with `ollama pull qwen3:1.7b`.

**Chat answer is overly long or uses technical headings**  
The RAG prompt has been updated to produce plain conversational answers. If you see old-style structured output, restart the backend to reload the updated prompt.

**Chat panel doesn't scroll as the answer streams in**  
Fixed — the chat now uses a `ResizeObserver` to track container height changes and scroll automatically as each token arrives.

**Frontend shows blank page**  
Make sure the backend is running on port 8000 before opening the frontend. Check the browser console for CORS errors.

**Forecast looks flat or inaccurate**  
The model needs enough seasonal variation to learn from. Use at least 24 months of data spanning more than one year. Including the full set of exogenous columns (temperature, rainfall, El Niño, etc.) significantly improves accuracy.
