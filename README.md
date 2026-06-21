# ⚡ WATT-IF

A locally-hosted Progressive Web App for forecasting household electricity consumption and cost.

Upload your monthly electricity bill history as a CSV, get SARIMAX-powered forecasts for the next 1, 3, or 6 months, and ask natural-language questions about your energy future — all running on your own machine.

**Stack:** FastAPI · pmdarima · ChromaDB · SQLite · Ollama (Qwen3 8B) · React · Vite · Recharts · vite-plugin-pwa

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 + | |
| Node.js | 18 + | |
| npm | 9 + | Comes with Node |
| Ollama | Latest | For the RAG chat feature |

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

> **Tip:** Use a virtual environment to keep things tidy:
> ```bash
> python -m venv .venv
> .venv\Scripts\activate   # Windows
> pip install -r requirements.txt
> ```

---

## 3. Install Ollama

Ollama runs the Qwen3 8B language model locally for the RAG chat feature.

1. Download the Windows installer from **https://ollama.com/download/windows**
2. Run `OllamaSetup.exe` — it installs silently and adds `ollama` to your PATH
3. Open a **new** terminal and pull the model:

```bash
ollama pull qwen3:8b
```

This downloads ~5 GB. Ollama starts as a background service automatically after install.

> The `/upload` and `/forecast` endpoints work without Ollama. Only the `/ask` (chat) feature requires it.

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

From the project root (`C:\Users\<you>\OneDrive\Desktop\WATT-IF`):

```bash
cd C:\Users\<you>\OneDrive\Desktop\WATT-IF
python -m uvicorn api.main:app --reload --port 8000
```

> **Important:** This command must be run from the project root — the folder that contains `api/`, `model/`, `pipeline/` etc. Running it from inside a subfolder (e.g. `frontend/`) will cause a `ModuleNotFoundError: No module named 'api'` error.

The API will be available at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

> The `--reload` flag auto-restarts the server when you change any Python file. If you update backend code manually, save the file and uvicorn will pick it up automatically.

### Terminal 2 — Frontend (React PWA)

From the `frontend/` directory:

```bash
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 6. Use the app

### Step 1 — Upload your bill data

Click **"Choose CSV"** and select a CSV file. The file must have these columns:

```
year_month,kwh,price
2023-01,342.5,89.20
2023-02,310.0,81.50
...
```

| Column | Format | Description |
|---|---|---|
| `year_month` | `YYYY-MM` | The billing month |
| `kwh` | Number | Total electricity consumed (kWh) |
| `price` | Number | Total bill amount |

- Minimum **14 rows** required to train the model
- 2–3 years of history (24–36 rows) gives the best forecast quality
- A synthetic test file is provided at `data/test_bills.csv`

### Step 2 — Generate a forecast

Click **1m**, **3m**, or **6m** to generate a forecast. The chart updates with:
- Monthly kWh consumption and price bars
- 95% confidence interval shaded bands

### Step 3 — Ask questions (requires Ollama)

Type a natural-language question in the chat panel, e.g.:
- *"Which month will have the highest consumption?"*
- *"What will my electricity bill be in March?"*
- *"How does my summer usage compare to winter?"*

---

## 7. Install as a PWA (optional)

For the full offline experience, run a production build:

```bash
# In the frontend/ directory
npm run build
npm run preview
```

Open **http://localhost:4173**. An install icon will appear in your browser's address bar — click it to install WATT-IF as a standalone desktop app. When offline, the app shows the most recently cached forecast data.

---

## Project structure

```
WATT-IF/
├── api/
│   ├── main.py              # FastAPI app — /upload, /forecast, /ask, /health
│   └── schemas.py           # Pydantic request/response models
├── pipeline/
│   ├── data_pipeline.py     # CSV ingestion, cleaning, SQLite persistence
│   ├── feature_engineering.py  # Weather + holiday enrichment (open-meteo)
│   └── models.py            # Shared dataclasses
├── model/
│   ├── sarimax_model.py     # SARIMAX training and forecasting
│   └── retraining.py        # Automatic retraining pipeline
├── storage/
│   ├── db.py                # SQLite schema and helpers
│   └── vector_store.py      # ChromaDB vector store (sentence-transformers)
├── rag/
│   └── rag_service.py       # RAG orchestration — retrieval + Ollama invocation
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Root component
│   │   ├── api/             # Typed API client + TypeScript types
│   │   └── components/      # ForecastChart, ChatPanel, UploadPanel, etc.
│   ├── vite.config.ts       # Vite + PWA configuration
│   └── package.json
├── data/
│   └── test_bills.csv       # Synthetic test data (36 months)
├── tests/                   # pytest + vitest test suites
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

With the backend running, visit `http://localhost:8000/health` to see the status of each subsystem:

```json
{
  "status": "ok",
  "subsystems": {
    "data_pipeline": "operational",
    "sarimax_model": "operational",
    "vector_store": "operational",
    "llm_service": "operational"
  }
}
```

`llm_service` will show `"degraded"` if Ollama is not running — everything else still works normally.

---

## Troubleshooting

**`ModuleNotFoundError` on startup**
Run `pip install -r requirements.txt` and make sure your virtual environment is activated.

**`SARIMAX artefact not found` on /forecast**
You need to upload a CSV first. The model trains automatically after a successful upload.

**Chat returns "LLM service unavailable"**
Ollama is not running. Start it with `ollama serve` or check that it is running as a background service. Make sure `qwen3:8b` has been pulled with `ollama pull qwen3:8b`.

**Frontend shows blank page**
Make sure the backend is running on port 8000 before opening the frontend. Check the browser console for CORS errors.

**Forecast looks flat / inaccurate**
The model needs enough seasonal variation to learn from. Use at least 24 months of data spanning more than one year, and make sure your kWh values reflect real seasonal patterns (higher in winter, lower in summer).
