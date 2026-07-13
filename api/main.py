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
import shutil
import sqlite3
import tempfile
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from api.auth import router as auth_router
from api.dependencies import get_current_user
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
    SavedForecastResponse,
    SaveForecastRequest,
    UploadResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
)
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

# Dynamically detect the machine's LAN IP for CORS, so you don't have to
# update this every time you connect to a different network.
def _get_local_ip() -> str:
    """Return the first non-loopback IPv4 address, or localhost as fallback."""
    import socket
    try:
        # Connect to an external address (doesn't actually send data) to
        # determine which local interface would be used.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

_LOCAL_IP = _get_local_ip()
PWA_ORIGIN_NETWORK = f"http://{_LOCAL_IP}:5173"
PWA_ORIGIN_NETWORK_PREVIEW = f"http://{_LOCAL_IP}:4173"

_HORIZON_LABELS: dict[int, str] = {1: "1m", 3: "3m", 6: "6m", 9: "9m", 12: "12m"}

# ---------------------------------------------------------------------------
# Background training state
# ---------------------------------------------------------------------------

_training_executor = ThreadPoolExecutor(max_workers=1)
_training_states: dict[int, dict] = {}  # keyed by user_id: {status, error}


def _get_training_state(user_id: int) -> dict:
    """Get the training state for a specific user."""
    return _training_states.get(user_id, {"status": "idle", "error": None})


def _run_retraining_background(previous_latest: str | None, user_id: int) -> None:
    """Run the full retraining pipeline in a background thread for a specific user."""
    _training_states[user_id] = {"status": "running", "error": None}
    try:
        conn = get_connection(DEFAULT_DB_PATH)
        init_db(conn)

        # Build user-specific model path
        user_model_path = Path("data/models") / str(user_id) / "sarimax_model.joblib"
        model = SARIMAXModel(artefact_path=user_model_path)

        # Scope training to user's records only
        from pipeline.feature_engineering import FeatureEngineeringService

        try:
            # Get training window from user's records only
            row = conn.execute(
                "SELECT MIN(year_month) as start, MAX(year_month) as end "
                "FROM monthly_bill_records WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if not row or not row["start"]:
                _training_states[user_id] = {"status": "failed", "error": "No records found for user."}
                conn.close()
                return

            start, end = row["start"], row["end"]
            # Get user's monthly records
            user_records = conn.execute(
                "SELECT year_month, kwh, price, meralco_rate, avg_temperature, "
                "avg_humidity, total_rainfall_mm, holiday_count, weekend_count, "
                "hot_days_count, rainy_days_count, is_el_nino "
                "FROM monthly_bill_records WHERE user_id = ? ORDER BY year_month",
                (user_id,),
            ).fetchall()

            from pipeline.models import MonthlyRecord
            monthly_records = [
                MonthlyRecord(
                    year_month=r["year_month"],
                    kwh=r["kwh"],
                    price=r["price"],
                    meralco_rate=r["meralco_rate"],
                    avg_temperature=r["avg_temperature"],
                    avg_humidity=r["avg_humidity"],
                    total_rainfall_mm=r["total_rainfall_mm"],
                    holiday_count=r["holiday_count"],
                    weekend_count=r["weekend_count"],
                    hot_days_count=r["hot_days_count"],
                    rainy_days_count=r["rainy_days_count"],
                    is_el_nino=r["is_el_nino"],
                )
                for r in user_records
            ]

            # Enrich and train
            feature_service = FeatureEngineeringService()
            enriched = feature_service.enrich(monthly_records)

            # Backup existing artefact if present
            backup_path = None
            try:
                backup_path = model.backup()
            except FileNotFoundError:
                pass

            training_result = model.train(enriched)

            # Delete backup on success
            if backup_path:
                try:
                    model.delete_backup(backup_path)
                except Exception:
                    pass

            # Write training log with user_id
            trained_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO training_log "
                "(trained_at, previous_mape, new_mape, training_window_start, "
                "training_window_end, user_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    trained_at,
                    None,
                    training_result.mape_validation,
                    training_result.training_window["start"],
                    training_result.training_window["end"],
                    user_id,
                ),
            )
            conn.commit()

            _training_states[user_id] = {"status": "done", "error": None}

            # Clear saved forecast since the model has changed — user needs
            # to generate a fresh forecast with the retrained model.
            try:
                conn2 = get_connection(DEFAULT_DB_PATH)
                init_db(conn2)
                conn2.execute(
                    "DELETE FROM saved_forecasts WHERE user_id = ?", (user_id,)
                )
                conn2.commit()
                conn2.close()
                logger.info("Cleared saved forecast for user %d after retraining.", user_id)
            except Exception as exc_sf:
                logger.warning("Failed to clear saved forecast for user %d: %s", user_id, exc_sf)
        except Exception as exc:
            logger.error("Background retraining failed for user %d: %s", user_id, exc, exc_info=True)
            _training_states[user_id] = {"status": "failed", "error": str(exc)}
        finally:
            conn.close()
    except Exception as exc:
        logger.error("Background retraining failed for user %d: %s", user_id, exc, exc_info=True)
        _training_states[user_id] = {"status": "failed", "error": str(exc)}

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
# Allow any origin so the frontend works from any device on the network.
# In production, restrict this to your actual deployment domain(s).
_cors_origins = os.environ.get("CORS_ORIGINS", "").strip()
if _cors_origins:
    _allowed_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
else:
    _allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Auth router (Req 2.1, 3.1) ───────────────────────────────────────────────
app.include_router(auth_router)


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
async def upload_csv(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)) -> UploadResponse:
    """Accept a monthly electricity bill CSV, validate, clean, and persist it.
    Retraining is kicked off in the background — poll GET /status to track progress.
    """
    user_id = current_user["id"]

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

            result = pipeline.ingest(file_path=tmp_path, user_id=user_id)
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
                "WHERE user_id = ? ORDER BY year_month",
                (user_id,),
            ).fetchall()
            year_months = [row["year_month"] for row in ingested_rows]
            # Remove stale CSV Upload entries for these months
            placeholders = ",".join("?" * len(year_months))
            conn.execute(
                f"DELETE FROM data_entry_log WHERE source = 'CSV Upload' "
                f"AND year_month IN ({placeholders}) AND user_id = ?",
                year_months + [user_id],
            )
            conn.executemany(
                "INSERT INTO data_entry_log "
                "(year_month, kwh, bill_amount, label, source, created_at, user_id) "
                "VALUES (?, ?, ?, NULL, 'CSV Upload', ?, ?)",
                [
                    (row["year_month"], row["kwh"], row["price"], created_at, user_id)
                    for row in ingested_rows
                ],
            )
            conn.commit()
            logger.info(
                "Mirrored %d CSV rows into data_entry_log for user %d.", len(ingested_rows), user_id,
            )
    finally:
        conn.close()

    # Upload succeeded — check user's auto-retrain preference.
    should_retrain = False
    conn2 = _get_db_conn()
    try:
        settings_row = conn2.execute(
            "SELECT auto_retrain_on_upload, min_datapoints_to_train "
            "FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if settings_row and settings_row["auto_retrain_on_upload"]:
            # Check minimum data points
            count_row = conn2.execute(
                "SELECT COUNT(*) as cnt FROM monthly_bill_records WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if count_row and count_row["cnt"] >= settings_row["min_datapoints_to_train"]:
                should_retrain = True
    finally:
        conn2.close()

    if should_retrain:
        _training_states[user_id] = {"status": "running", "error": None}
        _training_executor.submit(_run_retraining_background, None, user_id)

    return UploadResponse(
        rows_received=result.row_count,
        validation_status=result.validation_status,
        cleaning_report=result.cleaning_report,
        retraining_triggered=should_retrain,
    )


# ---------------------------------------------------------------------------
# GET /status  — poll training progress
# ---------------------------------------------------------------------------

@app.get("/status")
async def training_status(current_user: dict = Depends(get_current_user)) -> JSONResponse:
    """Return the current background training state for the authenticated user: idle | running | done | failed."""
    return JSONResponse(content=_get_training_state(current_user["id"]))


# ---------------------------------------------------------------------------
# POST /retrain  — manually trigger a full retrain on all available data
# ---------------------------------------------------------------------------

@app.post("/retrain")
async def retrain(current_user: dict = Depends(get_current_user)) -> JSONResponse:
    """Trigger a full model retrain unconditionally on the user's data in monthly_bill_records.

    Unlike the automatic trigger (which only fires when a new calendar month is
    detected), this endpoint retrains regardless — useful after data corrections
    or when the artefact has been deleted.

    Respects the user's min_datapoints_to_train setting.
    """
    user_id = current_user["id"]
    user_state = _get_training_state(user_id)
    if user_state["status"] == "running":
        return JSONResponse(
            status_code=409,
            content={"detail": "Training already in progress."},
        )

    # Check minimum data points from user settings
    conn = _get_db_conn()
    try:
        settings_row = conn.execute(
            "SELECT min_datapoints_to_train FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        min_points = settings_row["min_datapoints_to_train"] if settings_row else 12

        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM monthly_bill_records WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        actual_count = count_row["cnt"] if count_row else 0
    finally:
        conn.close()

    if actual_count < min_points:
        return JSONResponse(
            status_code=422,
            content={
                "detail": f"Not enough data to train. You have {actual_count} month(s) "
                          f"but need at least {min_points}. Adjust this in Settings."
            },
        )

    # Pass None as previous_latest so the new-month guard in check_and_retrain
    # is bypassed and the pipeline always runs.
    _training_states[user_id] = {"status": "running", "error": None}
    _training_executor.submit(_run_retraining_background, None, user_id)
    return JSONResponse(content={"status": "running"})


# ---------------------------------------------------------------------------
# POST /forecast  (Req 7.1, 4.5)
# ---------------------------------------------------------------------------

@app.post("/forecast", response_model=ForecastResponse)
async def forecast(request: ForecastRequest, current_user: dict = Depends(get_current_user)) -> ForecastResponse:
    """Generate a SARIMAX forecast and persist each month to the vector store."""
    user_id = current_user["id"]

    # Load model artefact from user's path.
    user_model_path = Path("data/models") / str(user_id) / "sarimax_model.joblib"
    if not user_model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not trained. Please train your model first.",
        )

    model = SARIMAXModel(artefact_path=user_model_path)
    try:
        model.load()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not trained. Please train your model first.",
        )

    # Load historical records scoped to user so the fallback exog estimator has real data.
    historical_enriched = None
    if request.exog is None:
        try:
            from pipeline.data_pipeline import DataPipeline
            from pipeline.feature_engineering import FeatureEngineeringService
            from pipeline.models import MonthlyRecord
            conn = _get_db_conn()
            try:
                # Get user's records only
                user_records = conn.execute(
                    "SELECT year_month, kwh, price, meralco_rate, avg_temperature, "
                    "avg_humidity, total_rainfall_mm, holiday_count, weekend_count, "
                    "hot_days_count, rainy_days_count, is_el_nino "
                    "FROM monthly_bill_records WHERE user_id = ? ORDER BY year_month",
                    (user_id,),
                ).fetchall()
                if user_records:
                    monthly_records = [
                        MonthlyRecord(
                            year_month=r["year_month"],
                            kwh=r["kwh"],
                            price=r["price"],
                            meralco_rate=r["meralco_rate"],
                            avg_temperature=r["avg_temperature"],
                            avg_humidity=r["avg_humidity"],
                            total_rainfall_mm=r["total_rainfall_mm"],
                            holiday_count=r["holiday_count"],
                            weekend_count=r["weekend_count"],
                            hot_days_count=r["hot_days_count"],
                            rainy_days_count=r["rainy_days_count"],
                            is_el_nino=r["is_el_nino"],
                        )
                        for r in user_records
                    ]
                    historical_enriched = FeatureEngineeringService().enrich(monthly_records)
                    logger.info(
                        "Loaded %d historical records for user %d for fallback exog estimation.",
                        len(historical_enriched), user_id,
                    )
                else:
                    logger.warning(
                        "No historical records found for user %d; fallback exog will use climate defaults.",
                        user_id,
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
            vector_store.upsert(doc, user_id=user_id)
        except Exception as exc:
            # Retry once (Req 4.7).
            logger.warning("First upsert attempt failed for %s: %s — retrying.", doc_id, exc)
            try:
                vector_store.upsert(doc, user_id=user_id)
            except Exception as exc2:
                logger.error("Retry upsert failed for %s: %s — continuing.", doc_id, exc2)

    # Check notification thresholds from user settings
    warnings: list[str] = []
    conn_w = _get_db_conn()
    try:
        settings_row = conn_w.execute(
            "SELECT notify_kwh_budget, notify_bill_ceiling, notify_high_consumption "
            "FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if settings_row:
            kwh_budget = settings_row["notify_kwh_budget"]
            bill_ceiling = settings_row["notify_bill_ceiling"]
            high_consumption = settings_row["notify_high_consumption"]
            for fm in months:
                if kwh_budget and fm.kwh_forecast > kwh_budget:
                    warnings.append(
                        f"{fm.year_month}: Forecasted {fm.kwh_forecast:.0f} kWh exceeds your budget of {kwh_budget:.0f} kWh"
                    )
                if bill_ceiling and fm.price_forecast > bill_ceiling:
                    warnings.append(
                        f"{fm.year_month}: Forecasted ₱{fm.price_forecast:.2f} exceeds your ceiling of ₱{bill_ceiling:.2f}"
                    )
                if high_consumption and fm.kwh_forecast > high_consumption:
                    warnings.append(
                        f"{fm.year_month}: High consumption alert — {fm.kwh_forecast:.0f} kWh exceeds {high_consumption:.0f} kWh threshold"
                    )
    except Exception:
        pass  # Non-critical — don't fail the forecast
    finally:
        conn_w.close()

    return ForecastResponse(horizon=request.horizon, months=months, warnings=warnings)


# ---------------------------------------------------------------------------
# GET /saved-forecast — load persisted forecast for current user
# ---------------------------------------------------------------------------

@app.get("/saved-forecast", response_model=SavedForecastResponse)
async def get_saved_forecast(current_user: dict = Depends(get_current_user)) -> SavedForecastResponse:
    """Return the user's most recently saved forecast, or empty if none exists."""
    import json

    user_id = current_user["id"]
    conn = _get_db_conn()
    try:
        row = conn.execute(
            "SELECT horizon, months, saved_at FROM saved_forecasts WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return SavedForecastResponse(horizon=None, months=None, saved_at=None)

    months_data = json.loads(row["months"])
    return SavedForecastResponse(horizon=row["horizon"], months=months_data, saved_at=row["saved_at"])


# ---------------------------------------------------------------------------
# POST /saved-forecast — persist forecast for current user
# ---------------------------------------------------------------------------

@app.post("/saved-forecast", response_model=SavedForecastResponse)
async def save_forecast(request: SaveForecastRequest, current_user: dict = Depends(get_current_user)) -> SavedForecastResponse:
    """Save the given forecast data for the authenticated user (upsert)."""
    import json

    user_id = current_user["id"]
    saved_at = datetime.now(timezone.utc).isoformat()
    months_json = json.dumps(request.months)

    conn = _get_db_conn()
    try:
        conn.execute(
            """INSERT INTO saved_forecasts (user_id, horizon, months, saved_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 horizon = excluded.horizon,
                 months = excluded.months,
                 saved_at = excluded.saved_at""",
            (user_id, request.horizon, months_json, saved_at),
        )
        conn.commit()
    finally:
        conn.close()

    return SavedForecastResponse(horizon=request.horizon, months=None, saved_at=saved_at)


# ---------------------------------------------------------------------------
# POST /ask  (Req 7.2, 6.9, 6.10)
# ---------------------------------------------------------------------------

@app.post("/ask")
async def ask(request: AskRequest, current_user: dict = Depends(get_current_user)) -> StreamingResponse:
    """Stream a natural-language answer about the electricity forecast via RAG.

    Response is text/event-stream (SSE).  Each event is a JSON object on a
    ``data:`` line in one of three shapes:

    * ``{"type": "token",  "text": "<delta>"}``   — one or more characters
    * ``{"type": "done",   "sources": [...]}``     — stream finished OK
    * ``{"type": "error",  "text": "<message>"}``  — stream finished with error
    """
    import asyncio

    user_id = current_user["id"]
    rag = RAGService()
    # stream_answer is a sync generator (httpx is sync).
    # Run it in a thread pool so it doesn't block the event loop, and
    # bridge each yielded SSE chunk into an async generator for StreamingResponse.
    sync_gen = rag.stream_answer(request.question, user_id=user_id)
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
async def model_info(current_user: dict = Depends(get_current_user)) -> ModelInfoResponse:
    """Return evaluation metrics and metadata for the currently trained model."""
    user_id = current_user["id"]
    user_model_path = Path("data/models") / str(user_id) / "sarimax_model.joblib"

    try:
        model = SARIMAXModel(artefact_path=user_model_path)
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
async def get_data_entries(current_user: dict = Depends(get_current_user)) -> list[DataEntryRow]:
    """Return all rows from data_entry_log joined with monthly_bill_records exog values."""
    conn = _get_db_conn()
    try:
        entries = conn.execute(
            "SELECT id, year_month, kwh, bill_amount, label, source, created_at "
            "FROM data_entry_log WHERE user_id = ? ORDER BY created_at DESC",
            (current_user["id"],),
        ).fetchall()
        result = []
        for entry in entries:
            mbr = conn.execute(
                "SELECT meralco_rate, avg_temperature, avg_humidity, total_rainfall_mm, "
                "holiday_count, weekend_count, hot_days_count, rainy_days_count, is_el_nino "
                "FROM monthly_bill_records WHERE year_month = ? AND user_id = ?",
                (entry["year_month"], current_user["id"]),
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


def _resolve_meralco_rate_for_month(year_month: str, conn: sqlite3.Connection, user_id: int | None = None) -> float:
    """Resolve the best available Meralco rate for a given year_month.

    Priority:
      0. User's rate_override from settings (if set)
      1. Live scraped rate (if year_month is the current or recent month)
      2. Exact match in monthly_bill_records for that year_month
      3. Most recent rate in monthly_bill_records
      4. Hardcoded default (₱11.80/kWh)
    """
    from scraper.meralco_rate import get_rate as _get_rate

    # Check user's rate override from settings
    if user_id is not None:
        settings_row = conn.execute(
            "SELECT rate_override FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if settings_row and settings_row["rate_override"] is not None:
            logger.info(
                "Using user rate override ₱%.4f/kWh for %s.", settings_row["rate_override"], year_month
            )
            return float(settings_row["rate_override"])

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

    # Exact match in DB for historical months (scoped to user if available)
    if user_id is not None:
        row = conn.execute(
            "SELECT meralco_rate FROM monthly_bill_records WHERE year_month = ? AND user_id = ?",
            (year_month, user_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT meralco_rate FROM monthly_bill_records WHERE year_month = ?",
            (year_month,),
        ).fetchone()
    if row and row[0]:
        return float(row[0])

    # Most recent rate in DB
    if user_id is not None:
        row = conn.execute(
            "SELECT meralco_rate FROM monthly_bill_records WHERE user_id = ? ORDER BY year_month DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT meralco_rate FROM monthly_bill_records ORDER BY year_month DESC LIMIT 1"
        ).fetchone()
    if row and row[0]:
        return float(row[0])

    return _PH_MERALCO_RATE_DEFAULT


def _resolve_exog_for_month(
    year_month: str,
    conn: sqlite3.Connection,
    user_id: int | None = None,
) -> dict[str, float]:
    """Build the best possible exogenous variable values for a given year_month.

    Weather variables (temperature, humidity, rainfall, rainy_days, hot_days):
      1. Open-Meteo API — real historical or forecast data for Manila
         (falls back gracefully to PAGASA priors if offline)

    Meralco rate uses its own priority chain (user override → live scrape → DB exact → DB latest → default).
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
        "meralco_rate":      _resolve_meralco_rate_for_month(year_month, conn, user_id=user_id),
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
    user_id: int | None = None,
) -> None:
    """Upsert a manual data entry into monthly_bill_records for model training.

    If rate_override is provided it is used directly instead of the auto-resolved rate.
    If bill_amount is provided it is used as price; otherwise price = kwh × rate.
    """
    exog = _resolve_exog_for_month(year_month, conn, user_id=user_id)

    # Rate: explicit override beats auto-resolved
    if rate_override is not None and rate_override > 0:
        exog["meralco_rate"] = rate_override

    price = bill_amount if bill_amount is not None else round(kwh * exog["meralco_rate"], 2)

    conn.execute(
        """
        INSERT INTO monthly_bill_records
            (year_month, kwh, price, meralco_rate, avg_temperature, avg_humidity,
             total_rainfall_mm, holiday_count, weekend_count, hot_days_count,
             rainy_days_count, is_el_nino, session_id, created_at, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, year_month) DO UPDATE SET
            kwh = excluded.kwh,
            price = excluded.price,
            meralco_rate = excluded.meralco_rate,
            avg_temperature = excluded.avg_temperature,
            avg_humidity = excluded.avg_humidity,
            total_rainfall_mm = excluded.total_rainfall_mm,
            holiday_count = excluded.holiday_count,
            weekend_count = excluded.weekend_count,
            hot_days_count = excluded.hot_days_count,
            rainy_days_count = excluded.rainy_days_count,
            is_el_nino = excluded.is_el_nino,
            session_id = excluded.session_id,
            created_at = excluded.created_at
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
            user_id,
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
async def create_data_entry(body: DataEntryCreate, current_user: dict = Depends(get_current_user)) -> DataEntryRow:
    """Persist a new data entry, bridge it into monthly_bill_records for training,
    and trigger background retraining if a new calendar month was added.
    """
    created_at = datetime.now(timezone.utc).isoformat()
    conn = _get_db_conn()
    try:
        # ── 0. Reject duplicate month for this user ───────────────────────────
        existing_entry = conn.execute(
            "SELECT id FROM data_entry_log WHERE year_month = ? AND user_id = ?",
            (body.year_month, current_user["id"]),
        ).fetchone()
        if existing_entry:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An entry for {body.year_month} already exists. "
                       f"Use the edit button to update it.",
            )

        # ── 1. Determine previous latest month before this entry ──────────────
        previous_latest: str | None = None
        try:
            from pipeline.data_pipeline import DataPipeline as _DP
            _, previous_latest = _DP(db_conn=conn).get_training_window_extent()
        except ValueError:
            previous_latest = None

        # ── 2. Write to data_entry_log ────────────────────────────────────────
        cursor = conn.execute(
            "INSERT INTO data_entry_log (year_month, kwh, bill_amount, label, source, created_at, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (body.year_month, body.kwh, body.bill_amount, body.label, body.source, created_at, current_user["id"]),
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
                user_id=current_user["id"],
            )

            # Backfill bill_amount in data_entry_log with the computed price
            # from monthly_bill_records so the history always shows a value.
            if body.bill_amount is None:
                mbr_price = conn.execute(
                    "SELECT price FROM monthly_bill_records WHERE year_month = ? AND user_id = ?",
                    (body.year_month, current_user["id"]),
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
            "FROM monthly_bill_records WHERE year_month = ? AND user_id = ?",
            (body.year_month, current_user["id"]),
        ).fetchone() if body.source == "Manual" else None

    finally:
        conn.close()

    # Auto-retraining removed — user must click Train Model explicitly.

    return _enrich_entry_row(row, mbr)


# ---------------------------------------------------------------------------
# PUT /data-entries/{id}  — update kWh, bill_amount, or label
# ---------------------------------------------------------------------------

@app.put("/data-entries/{entry_id}", response_model=DataEntryRow)
async def update_data_entry(entry_id: int, body: DataEntryUpdate, current_user: dict = Depends(get_current_user)) -> DataEntryRow:
    """Update kWh and/or bill_amount and/or label for an existing entry.

    Re-bridges the monthly_bill_records row with the new values and triggers
    background retraining so the model picks up the correction.
    """
    conn = _get_db_conn()
    try:
        existing = conn.execute(
            "SELECT id, year_month, kwh, bill_amount, label, source, created_at, user_id "
            "FROM data_entry_log WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found.")
        if existing["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

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
                user_id=current_user["id"],
            )

        row = conn.execute(
            "SELECT id, year_month, kwh, bill_amount, label, source, created_at "
            "FROM data_entry_log WHERE id = ?",
            (entry_id,),
        ).fetchone()
        mbr = conn.execute(
            "SELECT meralco_rate, avg_temperature, avg_humidity, total_rainfall_mm, "
            "holiday_count, weekend_count, hot_days_count, rainy_days_count, is_el_nino "
            "FROM monthly_bill_records WHERE year_month = ? AND user_id = ?",
            (existing["year_month"], current_user["id"]),
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
async def delete_data_entry(entry_id: int, current_user: dict = Depends(get_current_user)) -> Response:
    """Delete a data entry from the log.

    If no other log entry covers the same month, also removes the
    monthly_bill_records row (manual entries only) and triggers retraining.
    Returns 204 No Content on success.
    """
    conn = _get_db_conn()
    try:
        existing = conn.execute(
            "SELECT year_month, source, user_id FROM data_entry_log WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found.")
        if existing["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        conn.execute("DELETE FROM data_entry_log WHERE id = ?", (entry_id,))

        # Remove monthly_bill_records row only if no other entry covers this month for this user
        remaining = conn.execute(
            "SELECT COUNT(*) FROM data_entry_log WHERE year_month = ? AND user_id = ?",
            (existing["year_month"], current_user["id"]),
        ).fetchone()[0]
        if remaining == 0 and existing["source"] == "Manual":
            conn.execute(
                "DELETE FROM monthly_bill_records "
                "WHERE year_month = ? AND session_id = 'manual_entry' AND user_id = ?",
                (existing["year_month"], current_user["id"]),
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
async def clear_all_data(current_user: dict = Depends(get_current_user)) -> Response:
    """Permanently delete the current user's rows from monthly_bill_records,
    data_entry_log, training_log, and chat_history, and remove the user's
    trained model artefact from disk.

    This is a destructive, irreversible operation scoped to the authenticated
    user. The UI must present an explicit confirmation step before calling
    this endpoint.
    """
    user_id = current_user["id"]

    conn = _get_db_conn()
    try:
        conn.execute("DELETE FROM monthly_bill_records WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM data_entry_log WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM training_log WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        conn.commit()
        logger.warning(
            "All training data cleared for user %s via /data/all endpoint.", user_id
        )
    finally:
        conn.close()

    # Remove user's model artefact and directory
    user_model_dir = Path("data/models") / str(user_id)
    user_model_path = user_model_dir / "sarimax_model.joblib"
    try:
        if user_model_path.exists():
            user_model_path.unlink()
            logger.warning("Model artefact deleted for user %s: %s", user_id, user_model_path)
        if user_model_dir.exists():
            shutil.rmtree(user_model_dir)
            logger.warning("Model directory removed for user %s: %s", user_id, user_model_dir)
    except Exception as exc:
        logger.error("Could not delete model artefact for user %s: %s", user_id, exc)

    # Reset training state for this user
    _training_states.pop(user_id, None)

    return Response(status_code=204)


# ---------------------------------------------------------------------------
# GET /chat-history  (Req 5.2)
# ---------------------------------------------------------------------------

@app.get("/chat-history", response_model=list[ChatMessageRow])
async def get_chat_history(current_user: dict = Depends(get_current_user)) -> list[ChatMessageRow]:
    """Return the 100 most recent chat messages for the authenticated user, ordered by created_at ascending."""
    conn = _get_db_conn()
    try:
        rows = conn.execute(
            "SELECT id, role, text, created_at FROM ("
            "  SELECT id, role, text, created_at FROM chat_history"
            "  WHERE user_id = ?"
            "  ORDER BY created_at DESC LIMIT 100"
            ") ORDER BY created_at ASC",
            (current_user["id"],),
        ).fetchall()
    finally:
        conn.close()
    return [ChatMessageRow(**dict(row)) for row in rows]


# ---------------------------------------------------------------------------
# POST /chat-history  (Req 5.3)
# ---------------------------------------------------------------------------

@app.post("/chat-history", response_model=ChatMessageRow, status_code=201)
async def create_chat_message(body: ChatMessageCreate, current_user: dict = Depends(get_current_user)) -> ChatMessageRow:
    """Persist a new chat message for the authenticated user and return the created row with HTTP 201."""
    created_at = datetime.now(timezone.utc).isoformat()
    conn = _get_db_conn()
    try:
        cursor = conn.execute(
            "INSERT INTO chat_history (role, text, created_at, user_id) VALUES (?, ?, ?, ?)",
            (body.role, body.text, created_at, current_user["id"]),
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
async def clear_chat_history(current_user: dict = Depends(get_current_user)) -> Response:
    """Delete all chat messages for the authenticated user. Returns 204 No Content."""
    conn = _get_db_conn()
    try:
        conn.execute("DELETE FROM chat_history WHERE user_id = ?", (current_user["id"],))
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
    """Probe each subsystem and return operational / degraded status.

    All checks run concurrently via asyncio.to_thread to avoid sequential
    blocking on I/O-bound subsystem probes (disk, network, ChromaDB init).
    """
    import asyncio

    subsystems: dict[str, Literal["operational", "degraded"]] = {}
    model_trained_at: str | None = None
    last_upload_at: str | None = None

    # ── Define individual probes ──────────────────────────────────────────────

    def _check_data_pipeline() -> tuple[Literal["operational", "degraded"], str | None]:
        """Check SQLite + return last upload timestamp."""
        upload_ts: str | None = None
        try:
            conn = _get_db_conn()
            conn.execute("SELECT 1 FROM monthly_bill_records LIMIT 1")
            row = conn.execute(
                "SELECT MAX(created_at) FROM monthly_bill_records"
            ).fetchone()
            if row and row[0]:
                upload_ts = row[0]
            conn.close()
            return "operational", upload_ts
        except Exception as exc:
            logger.warning("Health: data_pipeline degraded — %s", exc)
            return "degraded", None

    def _check_sarimax() -> tuple[Literal["operational", "degraded"], str | None]:
        """Check model artefact can be loaded."""
        try:
            model = SARIMAXModel()
            model.load()
            artefact = model._artefact  # type: ignore[attr-defined]
            trained_at = artefact.get("trained_at") if artefact else None
            return "operational", trained_at
        except FileNotFoundError:
            return "degraded", None
        except Exception as exc:
            logger.warning("Health: sarimax_model degraded — %s", exc)
            return "degraded", None

    def _check_vector_store() -> Literal["operational", "degraded"]:
        """Check ChromaDB collection is accessible."""
        try:
            vs = VectorStore()
            vs.collection_size()
            return "operational"
        except Exception as exc:
            logger.warning("Health: vector_store degraded — %s", exc)
            return "degraded"

    def _check_ollama() -> Literal["operational", "degraded"]:
        """Check Ollama HTTP server is reachable."""
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(OLLAMA_HEALTH_URL)
                resp.raise_for_status()
            return "operational"
        except Exception as exc:
            logger.warning("Health: llm_service degraded — %s", exc)
            return "degraded"

    # ── Run all probes concurrently ───────────────────────────────────────────
    (
        (dp_status, upload_ts),
        (model_status, trained_at),
        vs_status,
        ollama_status,
    ) = await asyncio.gather(
        asyncio.to_thread(_check_data_pipeline),
        asyncio.to_thread(_check_sarimax),
        asyncio.to_thread(_check_vector_store),
        asyncio.to_thread(_check_ollama),
    )

    subsystems["data_pipeline"] = dp_status
    subsystems["sarimax_model"] = model_status
    subsystems["vector_store"] = vs_status
    subsystems["llm_service"] = ollama_status
    model_trained_at = trained_at
    last_upload_at = upload_ts

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


# ---------------------------------------------------------------------------
# GET /settings  — retrieve user preferences
# ---------------------------------------------------------------------------

@app.get("/settings", response_model=UserSettingsResponse)
async def get_settings(current_user: dict = Depends(get_current_user)) -> UserSettingsResponse:
    """Return the authenticated user's settings, creating defaults if none exist."""
    user_id = current_user["id"]
    conn = _get_db_conn()
    try:
        row = conn.execute(
            "SELECT customer_type, default_forecast_horizon, rate_override, "
            "chat_max_history, chat_auto_clear, notify_kwh_budget, "
            "notify_bill_ceiling, notify_high_consumption, "
            "auto_retrain_on_upload, min_datapoints_to_train "
            "FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if row is None:
            # Seed default settings for this user
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO user_settings (user_id, updated_at) VALUES (?, ?)",
                (user_id, now),
            )
            conn.commit()
            row = conn.execute(
                "SELECT customer_type, default_forecast_horizon, rate_override, "
                "chat_max_history, chat_auto_clear, notify_kwh_budget, "
                "notify_bill_ceiling, notify_high_consumption, "
                "auto_retrain_on_upload, min_datapoints_to_train "
                "FROM user_settings WHERE user_id = ?",
                (user_id,),
            ).fetchone()
    finally:
        conn.close()

    return UserSettingsResponse(
        customer_type=row["customer_type"],
        default_forecast_horizon=row["default_forecast_horizon"],
        rate_override=row["rate_override"],
        chat_max_history=row["chat_max_history"],
        chat_auto_clear=bool(row["chat_auto_clear"]),
        notify_kwh_budget=row["notify_kwh_budget"],
        notify_bill_ceiling=row["notify_bill_ceiling"],
        notify_high_consumption=row["notify_high_consumption"],
        auto_retrain_on_upload=bool(row["auto_retrain_on_upload"]),
        min_datapoints_to_train=row["min_datapoints_to_train"],
    )


# ---------------------------------------------------------------------------
# PUT /settings  — update user preferences
# ---------------------------------------------------------------------------

@app.put("/settings", response_model=UserSettingsResponse)
async def update_settings(body: UserSettingsUpdate, current_user: dict = Depends(get_current_user)) -> UserSettingsResponse:
    """Update the authenticated user's settings. Only provided fields are changed."""
    user_id = current_user["id"]
    conn = _get_db_conn()
    try:
        # Ensure row exists
        existing = conn.execute(
            "SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        now = datetime.now(timezone.utc).isoformat()
        if existing is None:
            conn.execute(
                "INSERT INTO user_settings (user_id, updated_at) VALUES (?, ?)",
                (user_id, now),
            )
            conn.commit()

        # Build SET clause dynamically for provided fields only
        updates: list[str] = []
        params: list = []

        if body.customer_type is not None:
            updates.append("customer_type = ?")
            params.append(body.customer_type)
        if body.default_forecast_horizon is not None:
            updates.append("default_forecast_horizon = ?")
            params.append(body.default_forecast_horizon)
        if "rate_override" in body.model_fields_set:
            updates.append("rate_override = ?")
            # Treat 0 as "disabled" → store as NULL
            params.append(body.rate_override if body.rate_override else None)
        if body.chat_max_history is not None:
            updates.append("chat_max_history = ?")
            params.append(body.chat_max_history)
        if body.chat_auto_clear is not None:
            updates.append("chat_auto_clear = ?")
            params.append(1 if body.chat_auto_clear else 0)
        if "notify_kwh_budget" in body.model_fields_set:
            updates.append("notify_kwh_budget = ?")
            params.append(body.notify_kwh_budget if body.notify_kwh_budget else None)
        if "notify_bill_ceiling" in body.model_fields_set:
            updates.append("notify_bill_ceiling = ?")
            params.append(body.notify_bill_ceiling if body.notify_bill_ceiling else None)
        if "notify_high_consumption" in body.model_fields_set:
            updates.append("notify_high_consumption = ?")
            params.append(body.notify_high_consumption if body.notify_high_consumption else None)
        if body.auto_retrain_on_upload is not None:
            updates.append("auto_retrain_on_upload = ?")
            params.append(1 if body.auto_retrain_on_upload else 0)
        if body.min_datapoints_to_train is not None:
            updates.append("min_datapoints_to_train = ?")
            params.append(body.min_datapoints_to_train)

        if updates:
            updates.append("updated_at = ?")
            params.append(now)
            params.append(user_id)
            conn.execute(
                f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?",
                params,
            )
            conn.commit()

        # Re-fetch and return
        row = conn.execute(
            "SELECT customer_type, default_forecast_horizon, rate_override, "
            "chat_max_history, chat_auto_clear, notify_kwh_budget, "
            "notify_bill_ceiling, notify_high_consumption, "
            "auto_retrain_on_upload, min_datapoints_to_train "
            "FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    return UserSettingsResponse(
        customer_type=row["customer_type"],
        default_forecast_horizon=row["default_forecast_horizon"],
        rate_override=row["rate_override"],
        chat_max_history=row["chat_max_history"],
        chat_auto_clear=bool(row["chat_auto_clear"]),
        notify_kwh_budget=row["notify_kwh_budget"],
        notify_bill_ceiling=row["notify_bill_ceiling"],
        notify_high_consumption=row["notify_high_consumption"],
        auto_retrain_on_upload=bool(row["auto_retrain_on_upload"]),
        min_datapoints_to_train=row["min_datapoints_to_train"],
    )
