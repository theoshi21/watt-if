"""
FastAPI application server for WATT-IF.

Exposes:
  POST /upload   — ingest a monthly electricity bill CSV (≤ 10 MB)
  POST /forecast — run SARIMAX forecast for horizon 1, 3, or 6 months
  POST /ask      — answer a natural-language question via the RAG service
  GET  /health   — probe all subsystems and report their status
  GET  /status   — check whether background model training is in progress

Requirements: 7.1 – 7.8, 6.9, 6.10, 10.2
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import tempfile
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from api.schemas import (
    AskRequest,
    AskResponse,
    ForecastRequest,
    ForecastResponse,
    HealthResponse,
    ModelInfoResponse,
    UploadResponse,
)
from model.retraining import RetrainingService
from model.sarimax_model import SARIMAXModel
from pipeline.data_pipeline import DataPipeline
from pipeline.models import ForecastDocument, ForecastMetadata
from rag.rag_service import RAGService
from storage.db import DEFAULT_DB_PATH, get_connection, init_db
from storage.vector_store import VectorStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
OLLAMA_HEALTH_URL = "http://localhost:11434"
PWA_ORIGIN = "http://localhost:5173"

_HORIZON_LABELS: dict[int, str] = {1: "1m", 3: "3m", 6: "6m"}

# ---------------------------------------------------------------------------
# Background training state
# ---------------------------------------------------------------------------

_training_executor = ThreadPoolExecutor(max_workers=1)
_training_state: dict = {"status": "idle", "error": None}  # idle | running | done | failed


def _run_retraining_background(previous_latest: str | None) -> None:
    """Run the full retraining pipeline in a background thread."""
    global _training_state
    _training_state = {"status": "running", "error": None}
    try:
        conn = get_connection(DEFAULT_DB_PATH)
        init_db(conn)
        svc = RetrainingService(db_conn=conn)
        result = svc.check_and_retrain(previous_latest_month=previous_latest)
        conn.close()
        if result.success:
            _training_state = {"status": "done", "error": None}
        else:
            _training_state = {"status": "failed", "error": result.error_message}
    except Exception as exc:
        logger.error("Background retraining failed: %s", exc, exc_info=True)
        _training_state = {"status": "failed", "error": str(exc)}

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="WATT-IF",
    description="Household electricity forecast API powered by SARIMAX + RAG.",
    version="1.0.0",
)


@app.on_event("startup")
async def warmup_ollama() -> None:
    """Send a minimal request to Ollama on startup so the model is loaded into
    memory before the first real user query arrives."""
    import asyncio
    import httpx as _httpx

    async def _ping() -> None:
        payload = {
            "model": "qwen3:1.7b",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": False,
            "keep_alive": -1,   # keep model resident after warmup
            "options": {"temperature": 0.1, "num_predict": 1},
        }
        try:
            async with _httpx.AsyncClient(timeout=180.0) as client:
                await client.post("http://localhost:11434/api/chat", json=payload)
            logger.info("Ollama warmup complete — model is loaded and ready.")
        except Exception as exc:
            logger.warning("Ollama warmup skipped (Ollama may not be running): %s", exc)

    asyncio.create_task(_ping())

# ── CORS (Req 7.6) ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[PWA_ORIGIN],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Global exception handler (Req 7.5) ───────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception for %s %s:\n%s",
        request.method,
        request.url,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_safe_filename(filename: str) -> bool:
    """Return False if *filename* contains path-traversal or injection patterns."""
    # Reject any filename containing path separators or null bytes.
    dangerous = re.compile(r"[/\\<>:\"'|?*\x00]|\.\.")
    return not dangerous.search(filename)


def _fmt_month(year_month: str) -> str:
    """Convert 'YYYY-MM' to 'Month YYYY' (e.g. '2024-05' → 'May 2024')."""
    from datetime import datetime
    try:
        return datetime.strptime(year_month, "%Y-%m").strftime("%B %Y")
    except ValueError:
        return year_month


def _build_forecast_doc_text(fm: ForecastMonth, horizon_label: str) -> str:
    """Build the rich human-readable forecast document text for RAG ingestion.

    Includes all exogenous variables and a natural-language "Forecast Drivers"
    paragraph so the RAG model can explain *why* the forecast is what it is.
    """
    readable = _fmt_month(fm.year_month)
    el_nino_status = "Active" if fm.is_el_nino else "Not active"

    # ── Forecast Drivers: build a natural-language interpretation ─────────────
    drivers: list[str] = []

    # Temperature influence
    if fm.avg_temperature >= 30:
        drivers.append(
            f"The average temperature of {fm.avg_temperature:.1f}°C is high, "
            f"which typically drives up electricity consumption through increased use of fans and air conditioners."
        )
    elif fm.avg_temperature < 27:
        drivers.append(
            f"The average temperature of {fm.avg_temperature:.1f}°C is relatively cool, "
            f"which may reduce the need for cooling appliances and lower electricity consumption."
        )
    else:
        drivers.append(
            f"The average temperature of {fm.avg_temperature:.1f}°C is moderate."
        )

    # Rainfall / cooling effect
    if fm.total_rainfall_mm > 200:
        drivers.append(
            f"High rainfall of {fm.total_rainfall_mm:.1f} mm and {fm.rainy_days_count} rainy day(s) "
            f"suggest cooler conditions that can moderate electricity demand."
        )
    elif fm.total_rainfall_mm < 50:
        drivers.append(
            f"Low rainfall of {fm.total_rainfall_mm:.1f} mm with only {fm.rainy_days_count} rainy day(s) "
            f"suggests dry, potentially hot conditions that may increase electricity consumption."
        )
    else:
        drivers.append(
            f"Rainfall is {fm.total_rainfall_mm:.1f} mm with {fm.rainy_days_count} rainy day(s)."
        )

    # Hot days
    if fm.hot_days_count >= 15:
        drivers.append(
            f"There are {fm.hot_days_count} hot day(s) this month, significantly increasing "
            f"the likelihood of higher cooling-related electricity consumption."
        )
    elif fm.hot_days_count > 0:
        drivers.append(
            f"There are {fm.hot_days_count} hot day(s) this month."
        )

    # El Niño
    if fm.is_el_nino:
        drivers.append(
            f"El Niño is active this month. El Niño periods are historically associated with "
            f"hotter and drier conditions in the Philippines, which tend to increase electricity consumption."
        )
    else:
        drivers.append(
            f"El Niño is not active this month. Normal weather conditions are expected."
        )

    # Meralco rate effect on bill
    drivers.append(
        f"The Meralco rate of ₱{fm.meralco_rate:.4f}/kWh directly determines the bill: "
        f"a higher rate increases the estimated bill even if consumption stays the same."
    )

    # Holidays / weekends (stay-home effect)
    if fm.holiday_count >= 3:
        drivers.append(
            f"This month has {fm.holiday_count} holiday(s) and {fm.weekend_count} weekend day(s). "
            f"More days at home can increase household electricity consumption."
        )
    else:
        drivers.append(
            f"This month has {fm.holiday_count} holiday(s) and {fm.weekend_count} weekend day(s)."
        )

    drivers_text = " ".join(drivers)

    return (
        f"Forecast for {readable} (horizon: {horizon_label}):\n"
        f"- Forecasted consumption: {fm.kwh_forecast:.2f} kWh "
        f"(95% CI: {fm.kwh_lower_95:.2f}–{fm.kwh_upper_95:.2f} kWh)\n"
        f"- Estimated electricity bill: ₱{fm.price_forecast:.2f} "
        f"(95% CI: ₱{fm.price_lower_95:.2f}–₱{fm.price_upper_95:.2f})\n"
        f"- Meralco rate: ₱{fm.meralco_rate:.4f}/kWh\n"
        f"- Average temperature: {fm.avg_temperature:.1f}°C\n"
        f"- Average humidity: {fm.avg_humidity:.1f}%\n"
        f"- Total rainfall: {fm.total_rainfall_mm:.1f} mm\n"
        f"- Holidays: {fm.holiday_count} | Weekends: {fm.weekend_count} | "
        f"Hot days: {fm.hot_days_count} | Rainy days: {fm.rainy_days_count}\n"
        f"- El Niño status: {el_nino_status}\n\n"
        f"Forecast Drivers: {drivers_text}"
    )


def _get_db_conn() -> sqlite3.Connection:
    """Open and initialise the application SQLite database."""
    conn = get_connection(DEFAULT_DB_PATH)
    init_db(conn)
    return conn


# ---------------------------------------------------------------------------
# POST /upload  (Req 7.3, 10.2)
# ---------------------------------------------------------------------------

@app.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)) -> UploadResponse:
    """Accept a monthly electricity bill CSV, validate, clean, and persist it.
    Retraining is kicked off in the background — poll GET /status to track progress.
    """

    filename = file.filename or ""
    if not _is_safe_filename(filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid filename '{filename}': path traversal or injection detected.")

    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Only .csv files are accepted.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File size {len(content)} bytes exceeds the 10 MB limit.")

    conn = _get_db_conn()
    try:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="wb") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            pipeline = DataPipeline(db_conn=conn)
            try:
                _, previous_latest = pipeline.get_training_window_extent()
            except ValueError:
                previous_latest = None

            result = pipeline.ingest(file_path=tmp_path)
        finally:
            os.unlink(tmp_path)
    finally:
        conn.close()

    # Fire retraining in background so upload returns immediately
    if result.validation_status == "ok" and result.row_count > 0:
        global _training_state
        if _training_state["status"] != "running":
            _training_state = {"status": "running", "error": None}
            _training_executor.submit(_run_retraining_background, previous_latest)

    return UploadResponse(
        rows_received=result.row_count,
        validation_status=result.validation_status,
        cleaning_report=result.cleaning_report,
        retraining_triggered=result.validation_status == "ok",
    )


# ---------------------------------------------------------------------------
# GET /status  — poll training progress
# ---------------------------------------------------------------------------

@app.get("/status")
async def training_status() -> JSONResponse:
    """Return the current background training state: idle | running | done | failed."""
    return JSONResponse(content=_training_state)


# ---------------------------------------------------------------------------
# POST /forecast  (Req 7.1, 4.5)
# ---------------------------------------------------------------------------

@app.post("/forecast", response_model=ForecastResponse)
async def forecast(request: ForecastRequest) -> ForecastResponse:
    """Generate a SARIMAX forecast and persist each month to the vector store."""

    # Load model artefact.
    model = SARIMAXModel()
    try:
        model.load()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    # Load historical records so the fallback exog estimator has real data.
    # These are only used when request.exog is None (the common case from the UI).
    historical_enriched = None
    if request.exog is None:
        try:
            from pipeline.data_pipeline import DataPipeline
            from pipeline.feature_engineering import FeatureEngineeringService
            conn = _get_db_conn()
            try:
                dp = DataPipeline(db_conn=conn)
                start, end = dp.get_training_window_extent()
                monthly_records = dp.get_monthly_records(start, end)
                historical_enriched = FeatureEngineeringService().enrich(monthly_records)
                logger.info(
                    "Loaded %d historical records for fallback exog estimation.",
                    len(historical_enriched),
                )
            except ValueError:
                logger.warning(
                    "No historical records found; fallback exog will use climate defaults."
                )
            finally:
                conn.close()
        except Exception as exc:
            logger.warning(
                "Could not load historical records for fallback exog: %s — "
                "proceeding with climate defaults.", exc,
            )

    # Run forecast.
    try:
        months = model.forecast(
            horizon=request.horizon,
            exog=request.exog,
            historical_records=historical_enriched,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # Upsert each ForecastMonth into the vector store (Req 4.5).
    horizon_label = _HORIZON_LABELS[request.horizon]
    vector_store = VectorStore()
    for fm in months:
        doc_id = f"{fm.year_month}_{horizon_label}"
        text = _build_forecast_doc_text(fm, horizon_label)
        doc = ForecastDocument(
            id=doc_id,
            text=text,
            metadata=ForecastMetadata(
                forecast_month=fm.year_month,
                forecasted_kwh=fm.kwh_forecast,
                forecasted_price=fm.price_forecast,
                horizon_label=horizon_label,
                meralco_rate=fm.meralco_rate,
                avg_temperature=fm.avg_temperature,
                avg_humidity=fm.avg_humidity,
                total_rainfall_mm=fm.total_rainfall_mm,
                holiday_count=fm.holiday_count,
                weekend_count=fm.weekend_count,
                hot_days_count=fm.hot_days_count,
                rainy_days_count=fm.rainy_days_count,
                is_el_nino=fm.is_el_nino,
            ),
        )
        try:
            vector_store.upsert(doc)
        except Exception as exc:
            # Retry once (Req 4.7).
            logger.warning("First upsert attempt failed for %s: %s — retrying.", doc_id, exc)
            try:
                vector_store.upsert(doc)
            except Exception as exc2:
                logger.error("Retry upsert failed for %s: %s — continuing.", doc_id, exc2)

    return ForecastResponse(horizon=request.horizon, months=months)


# ---------------------------------------------------------------------------
# POST /ask  (Req 7.2, 6.9, 6.10)
# ---------------------------------------------------------------------------

@app.post("/ask")
async def ask(request: AskRequest) -> StreamingResponse:
    """Stream a natural-language answer about the electricity forecast via RAG.

    Response is text/event-stream (SSE).  Each event is a JSON object on a
    ``data:`` line in one of three shapes:

    * ``{"type": "token",  "text": "<delta>"}``   — one or more characters
    * ``{"type": "done",   "sources": [...]}``     — stream finished OK
    * ``{"type": "error",  "text": "<message>"}``  — stream finished with error
    """
    import asyncio

    rag = RAGService()
    # stream_answer is a sync generator (httpx is sync).
    # Run it in a thread pool so it doesn't block the event loop, and
    # bridge each yielded SSE chunk into an async generator for StreamingResponse.
    sync_gen = rag.stream_answer(request.question)
    loop = asyncio.get_event_loop()

    async def _async_generate():
        while True:
            chunk = await loop.run_in_executor(None, next, sync_gen, None)
            if chunk is None:
                break
            yield chunk

    return StreamingResponse(
        _async_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# GET /model-info  — model evaluation metrics
# ---------------------------------------------------------------------------

def _mape_rating(mape_pct: float) -> str:
    """Convert a MAPE percentage to a human-readable accuracy rating."""
    if mape_pct < 5:
        return "Excellent"
    if mape_pct < 10:
        return "Good"
    if mape_pct < 20:
        return "Fair"
    return "Poor"


@app.get("/model-info", response_model=ModelInfoResponse)
async def model_info() -> ModelInfoResponse:
    """Return evaluation metrics and metadata for the currently trained model."""
    try:
        model = SARIMAXModel()
        model.load()
    except FileNotFoundError:
        return ModelInfoResponse(
            trained_at=None,
            mape_kwh_pct=None,
            mape_price_pct=None,
            mape_avg_pct=None,
            order=None,
            seasonal_order=None,
            training_window_start=None,
            training_window_end=None,
            rating=None,
        )

    art = model._artefact  # type: ignore[attr-defined]

    mape_avg = art.get("mape_validation")
    mape_avg_pct = round(mape_avg * 100, 2) if mape_avg is not None else None
    mape_kwh = art.get("mape_kwh")
    mape_kwh_pct = round(mape_kwh * 100, 2) if mape_kwh is not None else None
    mape_price = art.get("mape_price")
    mape_price_pct = round(mape_price * 100, 2) if mape_price is not None else None

    order = list(art.get("order", [])) or None
    seasonal_order = list(art.get("seasonal_order", [])) or None
    tw = art.get("training_window", {})

    return ModelInfoResponse(
        trained_at=art.get("trained_at"),
        mape_kwh_pct=mape_kwh_pct,
        mape_price_pct=mape_price_pct,
        mape_avg_pct=mape_avg_pct,
        order=order,
        seasonal_order=seasonal_order,
        training_window_start=tw.get("start"),
        training_window_end=tw.get("end"),
        rating=_mape_rating(mape_avg_pct) if mape_avg_pct is not None else None,
    )


# ---------------------------------------------------------------------------
# GET /health  (Req 7.7, 7.8)
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> JSONResponse:
    """Probe each subsystem and return operational / degraded status."""

    subsystems: dict[str, Literal["operational", "degraded"]] = {}

    # ── Data Pipeline / SQLite ────────────────────────────────────────────────
    try:
        conn = _get_db_conn()
        conn.execute("SELECT 1 FROM monthly_bill_records LIMIT 1")
        conn.close()
        subsystems["data_pipeline"] = "operational"
    except Exception as exc:
        logger.warning("Health: data_pipeline degraded — %s", exc)
        subsystems["data_pipeline"] = "degraded"

    # ── SARIMAX model artefact ────────────────────────────────────────────────
    model_trained_at: str | None = None
    try:
        model = SARIMAXModel()
        model.load()
        subsystems["sarimax_model"] = "operational"
        artefact = model._artefact  # type: ignore[attr-defined]
        if artefact:
            model_trained_at = artefact.get("trained_at")
    except FileNotFoundError:
        subsystems["sarimax_model"] = "degraded"
    except Exception as exc:
        logger.warning("Health: sarimax_model degraded — %s", exc)
        subsystems["sarimax_model"] = "degraded"

    # ── Last upload timestamp from SQLite ─────────────────────────────────────
    last_upload_at: str | None = None
    try:
        conn2 = _get_db_conn()
        row = conn2.execute(
            "SELECT MAX(created_at) FROM monthly_bill_records"
        ).fetchone()
        conn2.close()
        if row and row[0]:
            last_upload_at = row[0]
    except Exception:
        pass

    # ── Vector store / ChromaDB ───────────────────────────────────────────────
    try:
        vs = VectorStore()
        vs.collection_size()
        subsystems["vector_store"] = "operational"
    except Exception as exc:
        logger.warning("Health: vector_store degraded — %s", exc)
        subsystems["vector_store"] = "degraded"

    # ── LLM service / Ollama ─────────────────────────────────────────────────
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(OLLAMA_HEALTH_URL)
            resp.raise_for_status()
        subsystems["llm_service"] = "operational"
    except Exception as exc:
        logger.warning("Health: llm_service degraded — %s", exc)
        subsystems["llm_service"] = "degraded"

    all_ok = all(v == "operational" for v in subsystems.values())
    overall_status: Literal["ok", "degraded"] = "ok" if all_ok else "degraded"
    http_status = status.HTTP_200_OK if all_ok else status.HTTP_207_MULTI_STATUS

    return JSONResponse(
        status_code=http_status,
        content={
            **HealthResponse(
                status=overall_status,
                subsystems=subsystems,
            ).model_dump(),
            "model_trained_at": model_trained_at,
            "last_upload_at": last_upload_at,
        },
    )
