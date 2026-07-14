# User and Technical Documentation — WATT-IF

**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## Part A: End-User Instructions

### A.1 Overview

WATT-IF is a locally-hosted Progressive Web App (PWA) that forecasts household electricity consumption and cost for Filipino households. Users can upload bill history, generate forecasts, ask questions via an AI assistant, and calculate Meralco bill breakdowns.

### A.2 Getting Started

1. Open your browser and navigate to `http://localhost:5173`
2. The system auto-logs in with the default account (`wattif@gmail.com` / `wattif`)
3. To create your own account, click **Register** on the login page

### A.3 Uploading Data

1. Navigate to **Data Entry** from the sidebar
2. Choose one of:
   - **CSV Upload** — Select a CSV file with columns: `year_month`, `kwh`, `price` (max 10 MB)
   - **Manual Entry** — Select a month, enter kWh consumed, and optionally provide the bill amount
3. Weather, rate, and calendar variables are automatically resolved for each entry
4. A cleaning report confirms how many rows were processed

### A.4 Training the Model

1. On the **Data Entry** page, click **Train Model**
2. Minimum requirement: 14 months of data
3. Wait for the status indicator to show "Done"
4. The model evaluation (MAPE, accuracy rating) is displayed upon completion

### A.5 Generating Forecasts

1. Go to the **Forecast** page
2. Select a horizon: 1, 3, 6, 9, or 12 months
3. View the bar chart (kWh) and line chart (₱ bill) with 95% confidence intervals
4. Hover over chart elements for exact values
5. Warning cards appear if forecasts exceed your notification thresholds

### A.6 Using the Chat Assistant

1. Navigate to **Ask WATT-IF**
2. Type a question about your electricity data (e.g., "What's my bill for next month?")
3. The assistant streams its answer in real time, grounded in your actual forecast data
4. Requires Ollama to be running with the `qwen3:1.7b` model loaded

### A.7 Price Calculator

1. Go to **Price Calculator**
2. Enter your monthly kWh consumption
3. Select your customer type (Residential, General Service A, or B)
4. View the full charge-by-charge breakdown using the latest Meralco rate schedule

### A.8 Account Settings

- Change password, set customer type, default forecast horizon
- Configure notification thresholds (kWh budget, bill ceiling)
- Toggle auto-retrain on upload
- Clear chat history or all data (with confirmation)

---

## Part B: Technical Staff Instructions

### B.1 System Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React + TypeScript + Vite | User interface (SPA/PWA) |
| Backend | FastAPI (Python) | REST API, data pipeline, model orchestration |
| Database | SQLite (WAL mode) | User data, billing records, settings, chat history |
| Vector Store | ChromaDB | Forecast document embeddings for RAG retrieval |
| ML Model | SARIMAX (pmdarima) | Time-series forecasting with 9 exogenous variables |
| LLM | Ollama (qwen3:1.7b) | Natural-language answer generation |
| Scraper | pdfplumber + httpx | Meralco rate PDF parsing |

### B.2 Project Structure

```
WATT-IF/
├── api/              # FastAPI application (main.py, auth.py, schemas.py)
├── model/            # SARIMAX model training and forecasting
├── pipeline/         # Data pipeline (ingestion, enrichment, cleaning)
├── rag/              # RAG service (retrieval + LLM orchestration)
├── scraper/          # Meralco rate scraper
├── storage/          # SQLite DB init, vector store, EDA store
├── frontend/         # React app (src/, public/, dist/)
├── data/             # SQLite DB, ChromaDB, model artefacts, CSVs
├── tests/            # Selenium automation tests
├── Documentation/    # All project documentation
└── requirements.txt  # Python dependencies
```

### B.3 Installation

**Prerequisites:** Python 3.10+, Node.js 18+, Ollama (optional)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install frontend dependencies
cd frontend && npm install && cd ..

# 3. Configure environment
copy .env.example .env
# Edit .env: set JWT_SECRET=<your-secret>

# 4. Pull LLM model (optional, for chat)
ollama pull qwen3:1.7b
```

### B.4 Running the System

```bash
# Terminal 1: Backend
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

Access at `http://localhost:5173`

### B.5 Production Deployment (LAN)

```bash
# Backend (all interfaces)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend (build and serve)
cd frontend
npm run build
npm run preview -- --host 0.0.0.0 --port 4173
```

Access from any LAN device at `http://<host-ip>:4173`

### B.6 Database Schema

Key tables in SQLite (`data/wattif.db`):

| Table | Purpose |
|-------|---------|
| `users` | Account credentials (email, bcrypt hash) |
| `monthly_bill_records` | Primary data store (kWh, price, 9 exog vars, per user) |
| `data_entry_log` | Audit trail of all manual/CSV entries |
| `chat_history` | Persisted chat messages (role, text, timestamp) |
| `user_settings` | Per-user preferences and thresholds |
| `saved_forecasts` | Last generated forecast (JSON) |
| `training_log` | Model retraining history |

### B.7 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Authenticate and receive JWT |
| POST | `/upload` | Ingest a CSV file |
| POST | `/forecast` | Generate SARIMAX forecast |
| POST | `/ask` | Stream RAG chat answer (SSE) |
| POST | `/retrain` | Trigger model retraining |
| GET | `/health` | Probe all subsystems |
| GET | `/data-entries` | List all user data entries |
| GET | `/meralco-rate` | Fetch current rate schedule |
| GET | `/settings` | Get user preferences |
| PUT | `/settings` | Update user preferences |
| DELETE | `/data/all` | Clear all user data |

Full interactive docs: `http://localhost:8000/docs` (Swagger UI)

### B.8 Configuration

| Variable | Location | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | `.env` | `dev-secret-change-in-production` | Secret key for JWT signing |
| `VITE_API_BASE` | `frontend/.env.local` | Auto-detected | Backend URL override |
| Ollama model | `rag/rag_service.py` | `qwen3:1.7b` | LLM model name |
| Rate cache TTL | `scraper/meralco_rate.py` | 24 hours | Meralco rate refresh interval |
| Min data points | User Settings | 12 | Minimum records for training |

### B.9 Maintenance Tasks

| Task | Command / Action |
|------|-----------------|
| View system health | GET `http://localhost:8000/health` |
| Check model accuracy | GET `http://localhost:8000/model-info` |
| Force rate refresh | POST `http://localhost:8000/meralco-rate/refresh` |
| Run tests | `python -m pytest tests/ -q` |
| Regenerate synthetic data | `python data/generate_synthetic_2022_2025.py` |
| Backup database | Copy `data/wattif.db` to a safe location |
| Update Ollama model | `ollama pull qwen3:1.7b` |

### B.10 Troubleshooting

| Issue | Cause | Resolution |
|-------|-------|------------|
| Import errors on startup | Missing dependencies | Run `pip install -r requirements.txt` from project root |
| Forecast returns 503 | No trained model | Upload data → Train Model on Data Entry page |
| Chat shows "LLM unavailable" | Ollama not running | Run `ollama serve` and `ollama pull qwen3:1.7b` |
| CORS errors in browser | Backend not started | Start backend before frontend |
| Rate limiter lockout | 10 failed logins | Wait 15 minutes or restart backend |
| Flat/inaccurate forecasts | Insufficient data | Use 24+ months of data with exogenous columns |

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | July 2026 | Development Team | Initial document creation |
