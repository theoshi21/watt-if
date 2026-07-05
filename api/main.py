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
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from api.schemas import (
    AskRequest,
    AskResponse,
    ChatMessageCreate,
    ChatMessageRow,
    CustomerTypeResponse,
    DataEntryCreate,
    DataEntryRow,
    DataEntryUpdate,
    ForecastRequest,
    ForecastResponse,
    HealthResponse,
    MeralcoRateResponse,
    RateBracketResponse,
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
PWA_ORIGIN_NETWORK = f"http://192.168.254.108:4173"  # production preview on LAN

_HORIZON_LABELS: dict[int, str] = {1: "1m", 3: "3m", 6: "6m", 9: "9m", 12: "12m"}

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
    memory before the first real user query arrives.
    """
    import asyncio
    import httpx as _httpx

    async def _ping() -> None:
        payload = {
            "model": "qwen3:1.7b",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": False,
            "keep_alive": -1,
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
    allow_origins=[PWA_ORIGIN, PWA_ORIGIN_NETWORK],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

        # Mirror ingested rows into data_entry_log so Entry History shows them.
        # Delete existing 'CSV Upload' rows for those months first, then
        # re-insert, so re-uploading the same CSV doesn't create duplicates.
        # Manual entries for the same months are left untouched.
        if result.validation_status == "ok" and result.row_count > 0:
            created_at = datetime.now(timezone.utc).isoformat()
            ingested_rows = conn.execute(
                "SELECT year_month, kwh, price FROM monthly_bill_records "
                "ORDER BY year_month"
            ).fetchall()
            year_months = [row["year_month"] for row in ingested_rows]
            # Remove stale CSV Upload entries for these months
            placeholders = ",".join("?" * len(year_months))
            conn.execute(
                f"DELETE FROM data_entry_log WHERE source = 'CSV Upload' "
                f"AND year_month IN ({placeholders})",
                year_months,
            )
            conn.executemany(
                "INSERT INTO data_entry_log "
                "(year_month, kwh, bill_amount, label, source, created_at) "
                "VALUES (?, ?, ?, NULL, 'CSV Upload', ?)",
                [
                    (row["year_month"], row["kwh"], row["price"], created_at)
                    for row in ingested_rows
                ],
            )
            conn.commit()
            logger.info(
                "Mirrored %d CSV rows into data_entry_log.", len(ingested_rows)
            )
    finally:
        conn.close()

    # Upload succeeded — do NOT auto-retrain. User must click Train Model.
    return UploadResponse(
        rows_received=result.row_count,
        validation_status=result.validation_status,
        cleaning_report=result.cleaning_report,
        retraining_triggered=False,
    )


# ---------------------------------------------------------------------------
# GET /status  — poll training progress
# ---------------------------------------------------------------------------

@app.get("/status")
async def training_status() -> JSONResponse:
    """Return the current background training state: idle | running | done | failed."""
    return JSONResponse(content=_training_state)


# ---------------------------------------------------------------------------
# POST /retrain  — manually trigger a full retrain on all available data
# ---------------------------------------------------------------------------

@app.post("/retrain")
async def retrain() -> JSONResponse:
    """Trigger a full model retrain unconditionally on all data in monthly_bill_records.

    Unlike the automatic trigger (which only fires when a new calendar month is
    detected), this endpoint retrains regardless — useful after data corrections
    or when the artefact has been deleted.
    """
    global _training_state
    if _training_state["status"] == "running":
        return JSONResponse(
            status_code=409,
            content={"detail": "Training already in progress."},
        )

    # Pass None as previous_latest so the new-month guard in check_and_retrain
    # is bypassed and the pipeline always runs.
    _training_state = {"status": "running", "error": None}
    _training_executor.submit(_run_retraining_background, None)
    return JSONResponse(content={"status": "running"})


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
# GET /data-entries  (Req 4.2)
# ---------------------------------------------------------------------------

def _enrich_entry_row(entry_row: sqlite3.Row, mbr: sqlite3.Row | None) -> DataEntryRow:
    """Merge a data_entry_log row with its monthly_bill_records counterpart."""
    from scraper.enso import get_enso_phase as _enso_phase
    base = dict(entry_row)
    if mbr:
        mbr_dict = dict(mbr)
        base.update({
            "meralco_rate":      mbr_dict.get("meralco_rate"),
            "avg_temperature":   mbr_dict.get("avg_temperature"),
            "avg_humidity":      mbr_dict.get("avg_humidity"),
            "total_rainfall_mm": mbr_dict.get("total_rainfall_mm"),
            "holiday_count":     mbr_dict.get("holiday_count"),
            "weekend_count":     mbr_dict.get("weekend_count"),
            "hot_days_count":    mbr_dict.get("hot_days_count"),
            "rainy_days_count":  mbr_dict.get("rainy_days_count"),
            "is_el_nino":        mbr_dict.get("is_el_nino"),
            "enso_phase":        _enso_phase(base["year_month"]),
        })
    return DataEntryRow(**base)


@app.get("/data-entries", response_model=list[DataEntryRow])
async def get_data_entries() -> list[DataEntryRow]:
    """Return all rows from data_entry_log joined with monthly_bill_records exog values."""
    conn = _get_db_conn()
    try:
        entries = conn.execute(
            "SELECT id, year_month, kwh, bill_amount, label, source, created_at "
            "FROM data_entry_log ORDER BY created_at DESC"
        ).fetchall()
        result = []
        for entry in entries:
            mbr = conn.execute(
                "SELECT meralco_rate, avg_temperature, avg_humidity, total_rainfall_mm, "
                "holiday_count, weekend_count, hot_days_count, rainy_days_count, is_el_nino "
                "FROM monthly_bill_records WHERE year_month = ?",
                (entry["year_month"],),
            ).fetchone()
            result.append(_enrich_entry_row(entry, mbr))
    finally:
        conn.close()
    return result


# ---------------------------------------------------------------------------
# POST /data-entries  (Req 4.3)
# ---------------------------------------------------------------------------

# Philippine monthly climate priors (PAGASA Metro Manila normals).
# Last-resort fallback when NO historical data exists at all for a calendar month.
_PH_PRIORS: dict[str, dict[int, float]] = {
    "avg_temperature":   {1: 26.0, 2: 26.5, 3: 28.0, 4: 29.5, 5: 29.5,
                          6: 28.5, 7: 27.5, 8: 27.5, 9: 27.5, 10: 27.5,
                          11: 27.0, 12: 26.5},
    "avg_humidity":      {1: 78, 2: 76, 3: 74, 4: 74, 5: 78,
                          6: 82, 7: 85, 8: 85, 9: 84, 10: 82,
                          11: 80, 12: 79},
    "total_rainfall_mm": {1: 20,  2: 15,  3: 20,  4: 35,  5: 130,
                          6: 250, 7: 320, 8: 350, 9: 300, 10: 200,
                          11: 100, 12: 50},
    "hot_days_count":    {1: 4,  2: 5,  3: 12, 4: 18, 5: 17,
                          6: 10, 7: 6,  8: 6,  9: 7,  10: 8,
                          11: 7,  12: 5},
    "rainy_days_count":  {1: 5,  2: 4,  3: 5,  4: 7,  5: 14,
                          6: 20, 7: 24, 8: 23, 9: 22, 10: 18,
                          11: 13, 12: 9},
    "holiday_count":     {1: 1, 2: 1, 3: 1, 4: 2, 5: 2,
                          6: 2, 7: 1, 8: 2, 9: 1, 10: 1,
                          11: 2, 12: 4},
}
_PH_MERALCO_RATE_DEFAULT: float = 11.8  # ₱/kWh last-resort fallback


def _weekend_count_for_month(year: int, month: int) -> int:
    """Return the number of Saturday/Sunday days in a given calendar month."""
    import calendar as _calendar
    from datetime import date as _date
    _, days_in_month = _calendar.monthrange(year, month)
    return sum(
        1 for d in range(1, days_in_month + 1)
        if _date(year, month, d).weekday() >= 5
    )


def _resolve_meralco_rate_for_month(year_month: str, conn: sqlite3.Connection) -> float:
    """Resolve the best available Meralco rate for a given year_month.

    Priority:
      1. Live scraped rate (if year_month is the current or recent month)
      2. Exact match in monthly_bill_records for that year_month
      3. Most recent rate in monthly_bill_records
      4. Hardcoded default (₱11.80/kWh)
    """
    from scraper.meralco_rate import get_rate as _get_rate

    now = datetime.now(timezone.utc)
    current_ym = f"{now.year:04d}-{now.month:02d}"

    # Use live scraper for the current month or future months
    if year_month >= current_ym:
        try:
            result = _get_rate()
            residential = result.get_type("Residential")
            # Use the ">400 kWh" bracket residential_rate_per_kwh as the representative rate
            # (most households fall in higher brackets; adjust if needed)
            rate = residential.get_bracket_for_kwh(300).residential_rate_per_kwh
            if rate > 0:
                logger.info(
                    "Using live Meralco rate ₱%.4f/kWh for %s.", rate, year_month
                )
                return rate
        except Exception as exc:
            logger.warning("Live Meralco scrape failed for %s: %s — falling back.", year_month, exc)

    # Exact match in DB for historical months
    row = conn.execute(
        "SELECT meralco_rate FROM monthly_bill_records WHERE year_month = ?",
        (year_month,),
    ).fetchone()
    if row and row[0]:
        return float(row[0])

    # Most recent rate in DB
    row = conn.execute(
        "SELECT meralco_rate FROM monthly_bill_records ORDER BY year_month DESC LIMIT 1"
    ).fetchone()
    if row and row[0]:
        return float(row[0])

    return _PH_MERALCO_RATE_DEFAULT


def _resolve_exog_for_month(
    year_month: str,
    conn: sqlite3.Connection,
) -> dict[str, float]:
    """Build the best possible exogenous variable values for a given year_month.

    Weather variables (temperature, humidity, rainfall, rainy_days, hot_days):
      1. Open-Meteo API — real historical or forecast data for Manila
         (falls back gracefully to PAGASA priors if offline)

    Meralco rate uses its own priority chain (live scrape → DB exact → DB latest → default).
    Weekend count is always computed from the real calendar.
    is_el_nino is always 0 (cannot be determined automatically at entry time).
    """
    from scraper.weather import get_monthly_weather as _get_weather

    try:
        cal_month = int(year_month[5:7])
        cal_year = int(year_month[:4])
    except (ValueError, IndexError):
        cal_month = 1
        cal_year = datetime.now(timezone.utc).year

    # ── Fetch real weather data from Open-Meteo ───────────────────────────────
    weather = _get_weather(year_month)
    logger.info(
        "_resolve_exog_for_month %s: weather source=%s "
        "temp=%.1f hum=%.1f rain=%.1f rainy=%d hot=%d",
        year_month, weather.source,
        weather.avg_temperature, weather.avg_humidity,
        weather.total_rainfall_mm, weather.rainy_days_count, weather.hot_days_count,
    )

    # ── ENSO phase from NOAA ONI lookup ───────────────────────────────────────
    from scraper.enso import get_is_el_nino as _get_el_nino
    is_el_nino = float(_get_el_nino(year_month))

    return {
        "meralco_rate":      _resolve_meralco_rate_for_month(year_month, conn),
        "avg_temperature":   weather.avg_temperature,
        "avg_humidity":      weather.avg_humidity,
        "total_rainfall_mm": weather.total_rainfall_mm,
        "holiday_count":     float(_PH_PRIORS["holiday_count"][cal_month]),
        "weekend_count":     float(_weekend_count_for_month(cal_year, cal_month)),
        "hot_days_count":    float(weather.hot_days_count),
        "rainy_days_count":  float(weather.rainy_days_count),
        "is_el_nino":        is_el_nino,
    }


def _bridge_entry_to_bill_records(
    conn: sqlite3.Connection,
    year_month: str,
    kwh: float,
    bill_amount: float | None,
    rate_override: float | None,
    created_at: str,
) -> None:
    """Upsert a manual data entry into monthly_bill_records for model training.

    If rate_override is provided it is used directly instead of the auto-resolved rate.
    If bill_amount is provided it is used as price; otherwise price = kwh × rate.
    """
    exog = _resolve_exog_for_month(year_month, conn)

    # Rate: explicit override beats auto-resolved
    if rate_override is not None and rate_override > 0:
        exog["meralco_rate"] = rate_override

    price = bill_amount if bill_amount is not None else round(kwh * exog["meralco_rate"], 2)

    conn.execute(
        """
        INSERT OR REPLACE INTO monthly_bill_records
            (year_month, kwh, price, meralco_rate, avg_temperature, avg_humidity,
             total_rainfall_mm, holiday_count, weekend_count, hot_days_count,
             rainy_days_count, is_el_nino, session_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            year_month,
            kwh,
            price,
            exog["meralco_rate"],
            exog["avg_temperature"],
            exog["avg_humidity"],
            exog["total_rainfall_mm"],
            int(exog["holiday_count"]),
            int(exog["weekend_count"]),
            int(exog["hot_days_count"]),
            int(exog["rainy_days_count"]),
            int(exog["is_el_nino"]),
            "manual_entry",
            created_at,
        ),
    )
    conn.commit()
    logger.info(
        "Bridged manual entry %s (%.2f kWh, ₱%.2f) into monthly_bill_records. "
        "Exog: rate=%.4f temp=%.1f hum=%.1f rain=%.1f holidays=%d weekends=%d "
        "hot=%d rainy=%d el_nino=%d",
        year_month, kwh, price,
        exog["meralco_rate"], exog["avg_temperature"], exog["avg_humidity"],
        exog["total_rainfall_mm"], int(exog["holiday_count"]), int(exog["weekend_count"]),
        int(exog["hot_days_count"]), int(exog["rainy_days_count"]), int(exog["is_el_nino"]),
    )


@app.post("/data-entries", response_model=DataEntryRow, status_code=201)
async def create_data_entry(body: DataEntryCreate) -> DataEntryRow:
    """Persist a new data entry, bridge it into monthly_bill_records for training,
    and trigger background retraining if a new calendar month was added.
    """
    created_at = datetime.now(timezone.utc).isoformat()
    conn = _get_db_conn()
    try:
        # ── 1. Determine previous latest month before this entry ──────────────
        previous_latest: str | None = None
        try:
            from pipeline.data_pipeline import DataPipeline as _DP
            _, previous_latest = _DP(db_conn=conn).get_training_window_extent()
        except ValueError:
            previous_latest = None

        # ── 2. Write to data_entry_log ────────────────────────────────────────
        cursor = conn.execute(
            "INSERT INTO data_entry_log (year_month, kwh, bill_amount, label, source, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (body.year_month, body.kwh, body.bill_amount, body.label, body.source, created_at),
        )
        conn.commit()
        row_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, year_month, kwh, bill_amount, label, source, created_at "
            "FROM data_entry_log WHERE id = ?",
            (row_id,),
        ).fetchone()

        # ── 3. Bridge into monthly_bill_records (Manual entries only) ─────────
        if body.source == "Manual":
            _bridge_entry_to_bill_records(
                conn,
                year_month=body.year_month,
                kwh=body.kwh,
                bill_amount=body.bill_amount,
                rate_override=body.rate_override,
                created_at=created_at,
            )

            # Backfill bill_amount in data_entry_log with the computed price
            # from monthly_bill_records so the history always shows a value.
            if body.bill_amount is None:
                mbr_price = conn.execute(
                    "SELECT price FROM monthly_bill_records WHERE year_month = ?",
                    (body.year_month,),
                ).fetchone()
                if mbr_price:
                    conn.execute(
                        "UPDATE data_entry_log SET bill_amount = ? WHERE id = ?",
                        (mbr_price["price"], row_id),
                    )
                    conn.commit()
                    # Re-fetch the row with the updated bill_amount
                    row = conn.execute(
                        "SELECT id, year_month, kwh, bill_amount, label, source, created_at "
                        "FROM data_entry_log WHERE id = ?",
                        (row_id,),
                    ).fetchone()

        # Fetch enriched exog fields after bridge
        mbr = conn.execute(
            "SELECT meralco_rate, avg_temperature, avg_humidity, total_rainfall_mm, "
            "holiday_count, weekend_count, hot_days_count, rainy_days_count, is_el_nino "
            "FROM monthly_bill_records WHERE year_month = ?",
            (body.year_month,),
        ).fetchone() if body.source == "Manual" else None

    finally:
        conn.close()

    # Auto-retraining removed — user must click Train Model explicitly.

    return _enrich_entry_row(row, mbr)


# ---------------------------------------------------------------------------
# PUT /data-entries/{id}  — update kWh, bill_amount, or label
# ---------------------------------------------------------------------------

@app.put("/data-entries/{entry_id}", response_model=DataEntryRow)
async def update_data_entry(entry_id: int, body: DataEntryUpdate) -> DataEntryRow:
    """Update kWh and/or bill_amount and/or label for an existing entry.

    Re-bridges the monthly_bill_records row with the new values and triggers
    background retraining so the model picks up the correction.
    """
    conn = _get_db_conn()
    try:
        existing = conn.execute(
            "SELECT id, year_month, kwh, bill_amount, label, source, created_at "
            "FROM data_entry_log WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found.")

        # body fields: None means "not provided, keep existing"; use model_fields_set
        # to distinguish "explicitly sent null" from "not sent at all".
        new_kwh   = body.kwh         if "kwh"         in body.model_fields_set else existing["kwh"]
        new_bill  = body.bill_amount if "bill_amount" in body.model_fields_set else existing["bill_amount"]
        new_label = body.label       if "label"       in body.model_fields_set else existing["label"]

        # kWh must always be a positive number
        if new_kwh is None or new_kwh <= 0:
            raise HTTPException(status_code=422, detail="kwh must be a positive number.")

        conn.execute(
            "UPDATE data_entry_log SET kwh = ?, bill_amount = ?, label = ? WHERE id = ?",
            (new_kwh, new_bill, new_label, entry_id),
        )
        conn.commit()

        # Re-bridge so monthly_bill_records reflects the updated values
        if existing["source"] == "Manual":
            _bridge_entry_to_bill_records(
                conn,
                year_month=existing["year_month"],
                kwh=new_kwh,
                bill_amount=new_bill,
                rate_override=None,
                created_at=existing["created_at"],
            )

        row = conn.execute(
            "SELECT id, year_month, kwh, bill_amount, label, source, created_at "
            "FROM data_entry_log WHERE id = ?",
            (entry_id,),
        ).fetchone()
        mbr = conn.execute(
            "SELECT meralco_rate, avg_temperature, avg_humidity, total_rainfall_mm, "
            "holiday_count, weekend_count, hot_days_count, rainy_days_count, is_el_nino "
            "FROM monthly_bill_records WHERE year_month = ?",
            (existing["year_month"],),
        ).fetchone()

        previous_latest_upd: str | None = None
        try:
            from pipeline.data_pipeline import DataPipeline as _DP
            _, previous_latest_upd = _DP(db_conn=conn).get_training_window_extent()
        except ValueError:
            pass

    finally:
        conn.close()

    return _enrich_entry_row(row, mbr)


# ---------------------------------------------------------------------------
# DELETE /data-entries/{id}
# ---------------------------------------------------------------------------

@app.delete("/data-entries/{entry_id}", status_code=204, response_class=Response)
async def delete_data_entry(entry_id: int) -> Response:
    """Delete a data entry from the log.

    If no other log entry covers the same month, also removes the
    monthly_bill_records row (manual entries only) and triggers retraining.
    Returns 204 No Content on success.
    """
    conn = _get_db_conn()
    try:
        existing = conn.execute(
            "SELECT year_month, source FROM data_entry_log WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found.")

        conn.execute("DELETE FROM data_entry_log WHERE id = ?", (entry_id,))

        # Remove monthly_bill_records row only if no other entry covers this month
        remaining = conn.execute(
            "SELECT COUNT(*) FROM data_entry_log WHERE year_month = ?",
            (existing["year_month"],),
        ).fetchone()[0]
        if remaining == 0 and existing["source"] == "Manual":
            conn.execute(
                "DELETE FROM monthly_bill_records "
                "WHERE year_month = ? AND session_id = 'manual_entry'",
                (existing["year_month"],),
            )

        conn.commit()

        previous_latest_del: str | None = None
        try:
            from pipeline.data_pipeline import DataPipeline as _DP
            _, previous_latest_del = _DP(db_conn=conn).get_training_window_extent()
        except ValueError:
            pass

    finally:
        conn.close()

    return Response(status_code=204)


# ---------------------------------------------------------------------------
# DELETE /data/all  — wipe all training data and the model artefact
# ---------------------------------------------------------------------------

@app.delete("/data/all", status_code=204, response_class=Response)
async def clear_all_data() -> Response:
    """Permanently delete all rows from monthly_bill_records and data_entry_log,
    and remove the trained model artefact from disk.

    This is a destructive, irreversible operation. The UI must present an
    explicit confirmation step before calling this endpoint.
    """
    from model.sarimax_model import SARIMAXModel as _Model

    conn = _get_db_conn()
    try:
        conn.execute("DELETE FROM monthly_bill_records")
        conn.execute("DELETE FROM data_entry_log")
        conn.commit()
        logger.warning("All training data cleared via /data/all endpoint.")
    finally:
        conn.close()

    # Remove artefact so the model reports 'not trained'
    artefact_path = _Model()._artefact_path  # type: ignore[attr-defined]
    try:
        if artefact_path.exists():
            artefact_path.unlink()
            logger.warning("Model artefact deleted: %s", artefact_path)
    except Exception as exc:
        logger.error("Could not delete model artefact: %s", exc)

    # Reset training state
    global _training_state
    _training_state = {"status": "idle", "error": None}

    return Response(status_code=204)


# ---------------------------------------------------------------------------
# GET /chat-history  (Req 5.2)
# ---------------------------------------------------------------------------

@app.get("/chat-history", response_model=list[ChatMessageRow])
async def get_chat_history() -> list[ChatMessageRow]:
    """Return the 100 most recent chat messages ordered by created_at ascending."""
    conn = _get_db_conn()
    try:
        rows = conn.execute(
            "SELECT id, role, text, created_at FROM ("
            "  SELECT id, role, text, created_at FROM chat_history"
            "  ORDER BY created_at DESC LIMIT 100"
            ") ORDER BY created_at ASC"
        ).fetchall()
    finally:
        conn.close()
    return [ChatMessageRow(**dict(row)) for row in rows]


# ---------------------------------------------------------------------------
# POST /chat-history  (Req 5.3)
# ---------------------------------------------------------------------------

@app.post("/chat-history", response_model=ChatMessageRow, status_code=201)
async def create_chat_message(body: ChatMessageCreate) -> ChatMessageRow:
    """Persist a new chat message and return the created row with HTTP 201."""
    created_at = datetime.now(timezone.utc).isoformat()
    conn = _get_db_conn()
    try:
        cursor = conn.execute(
            "INSERT INTO chat_history (role, text, created_at) VALUES (?, ?, ?)",
            (body.role, body.text, created_at),
        )
        conn.commit()
        row_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, role, text, created_at FROM chat_history WHERE id = ?",
            (row_id,),
        ).fetchone()
    finally:
        conn.close()
    return ChatMessageRow(**dict(row))


# ---------------------------------------------------------------------------
# DELETE /chat-history  — wipe all chat messages
# ---------------------------------------------------------------------------

@app.delete("/chat-history", status_code=204, response_class=Response)
async def clear_chat_history() -> Response:
    """Delete all rows from chat_history. Returns 204 No Content."""
    conn = _get_db_conn()
    try:
        conn.execute("DELETE FROM chat_history")
        conn.commit()
    finally:
        conn.close()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# GET /meralco-rate  — current Meralco residential rate (cached 24 h)
# ---------------------------------------------------------------------------

@app.get("/meralco-rate", response_model=MeralcoRateResponse)
async def meralco_rate() -> MeralcoRateResponse:
    """Return the current Meralco residential rate.

    Result is cached for 24 hours. Returns hardcoded fallback values if the
    live scrape fails, so the calculator always has a usable rate.
    """
    from scraper.meralco_rate import get_rate
    result = get_rate()
    return MeralcoRateResponse(
        customer_types=[
            CustomerTypeResponse(
                type_key=ct.type_key,
                type_label=ct.type_label,
                brackets=[RateBracketResponse(**b.__dict__) for b in ct.brackets],
            )
            for ct in result.customer_types
        ],
        fetched_at=result.fetched_at,
        is_fallback=result.is_fallback,
        effective_month=result.effective_month,
    )


# ---------------------------------------------------------------------------
# POST /meralco-rate/refresh  — force a fresh scrape, bypass cache
# ---------------------------------------------------------------------------

@app.post("/meralco-rate/refresh", response_model=MeralcoRateResponse)
async def meralco_rate_refresh() -> MeralcoRateResponse:
    """Force a fresh scrape of the Meralco rate, bypassing the 24-hour cache."""
    from scraper.meralco_rate import refresh_rate
    result = refresh_rate()
    return MeralcoRateResponse(
        customer_types=[
            CustomerTypeResponse(
                type_key=ct.type_key,
                type_label=ct.type_label,
                brackets=[RateBracketResponse(**b.__dict__) for b in ct.brackets],
            )
            for ct in result.customer_types
        ],
        fetched_at=result.fetched_at,
        is_fallback=result.is_fallback,
        effective_month=result.effective_month,
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
