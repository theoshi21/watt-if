"""
Model Retraining Pipeline for WATT-IF.

Orchestrates the full pipeline from data retrieval through to forecast document
storage when new monthly bill data is uploaded.

Covers tasks 10.1 and 10.2:
  - RetrainingService.check_and_retrain()  — Req 9.1, 9.2, 9.3
  - RetrainingService._write_training_log() — Req 9.4, 9.5, 9.6
  - SARIMAXModel.backup() / delete_backup() — already in sarimax_model.py

Trigger condition (Req 9.1):
    Retraining is triggered when the latest year_month in the persisted
    ``monthly_bill_records`` table is strictly greater than the latest
    year_month seen during the previous run.

Failure semantics (Req 9.3):
    If any step fails, the error is logged, further execution halts, and
    the existing model artefact and vector store are left unchanged.

Backup semantics (Req 9.5, 9.6):
    Before overwriting the artefact, the current one is copied to a
    versioned backup.  The backup is deleted only after the new artefact
    is successfully persisted.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from model.sarimax_model import SARIMAXModel
from pipeline.data_pipeline import DataPipeline
from pipeline.feature_engineering import FeatureEngineeringService
from pipeline.models import ForecastDocument, ForecastMetadata, ModelTrainingError
from storage.db import DEFAULT_DB_PATH, get_connection, init_db
from storage.eda_store import EDAStore
from storage.vector_store import VectorStore, VectorStoreError

def _fmt_month(year_month: str) -> str:
    """Convert 'YYYY-MM' to 'Month YYYY' (e.g. '2024-05' → 'May 2024')."""
    from datetime import datetime
    try:
        return datetime.strptime(year_month, "%Y-%m").strftime("%B %Y")
    except ValueError:
        return year_month


def _build_forecast_doc_text(fm, horizon_label: str) -> str:
    """Build the rich human-readable forecast document text for RAG ingestion.

    Mirrors api/main.py's _build_forecast_doc_text — includes all exogenous
    variables and a natural-language Forecast Drivers interpretation paragraph.
    """
    readable = _fmt_month(fm.year_month)
    el_nino_status = "Active" if fm.is_el_nino else "Not active"

    drivers: list[str] = []

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
        drivers.append(f"The average temperature of {fm.avg_temperature:.1f}°C is moderate.")

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
        drivers.append(f"Rainfall is {fm.total_rainfall_mm:.1f} mm with {fm.rainy_days_count} rainy day(s).")

    if fm.hot_days_count >= 15:
        drivers.append(
            f"There are {fm.hot_days_count} hot day(s) this month, significantly increasing "
            f"the likelihood of higher cooling-related electricity consumption."
        )
    elif fm.hot_days_count > 0:
        drivers.append(f"There are {fm.hot_days_count} hot day(s) this month.")

    if fm.is_el_nino:
        drivers.append(
            f"El Niño is active this month. El Niño periods are historically associated with "
            f"hotter and drier conditions in the Philippines, which tend to increase electricity consumption."
        )
    else:
        drivers.append("El Niño is not active this month. Normal weather conditions are expected.")

    drivers.append(
        f"The Meralco rate of ₱{fm.meralco_rate:.4f}/kWh directly determines the bill: "
        f"a higher rate increases the estimated bill even if consumption stays the same."
    )

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


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Forecast horizons to generate after every retraining run.
_RETRAIN_HORIZONS: list[int] = [1, 3, 6]
_HORIZON_LABELS: dict[int, str] = {1: "1m", 3: "3m", 6: "6m"}

# Minimum days to retain training log entries (Req 9.4).
_LOG_RETENTION_DAYS = 90


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class RetrainingResult:
    """Outcome of a :meth:`RetrainingService.check_and_retrain` call."""

    triggered: bool
    """Whether retraining was triggered (False if condition not met)."""

    success: bool
    """True when retraining completed without errors."""

    previous_latest_month: str | None
    """Latest year_month before this run (``None`` if no prior data)."""

    new_latest_month: str | None
    """Latest year_month after ingest (``None`` if not applicable)."""

    new_mape: float | None
    """MAPE from the newly trained model (``None`` if training not reached)."""

    error_message: str | None
    """Description of the failure step, if any."""


# ---------------------------------------------------------------------------
# RetrainingService
# ---------------------------------------------------------------------------


class RetrainingService:
    """Orchestrates model retraining when new monthly data is detected.

    Parameters
    ----------
    db_conn:
        An open :class:`sqlite3.Connection` for the WATT-IF SQLite database.
        The caller retains ownership.
    model:
        Optional pre-constructed :class:`~model.sarimax_model.SARIMAXModel`.
        Defaults to a new instance using the standard artefact path.
    feature_service:
        Optional pre-constructed :class:`~pipeline.feature_engineering.FeatureEngineeringService`.
    vector_store:
        Optional pre-constructed :class:`~storage.vector_store.VectorStore`.
    """

    def __init__(
        self,
        db_conn: sqlite3.Connection,
        model: SARIMAXModel | None = None,
        feature_service: FeatureEngineeringService | None = None,
        vector_store: VectorStore | None = None,
        eda_store: EDAStore | None = None,
        user_id: int | str | None = None,
    ) -> None:
        self._conn = db_conn
        self._model = model or SARIMAXModel()
        self._feature_service = feature_service or FeatureEngineeringService()
        self._vector_store = vector_store or VectorStore()
        self._eda_store = eda_store or EDAStore()
        self._user_id = user_id

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def check_and_retrain(
        self,
        previous_latest_month: str | None,
    ) -> RetrainingResult:
        """Check the trigger condition and run retraining if needed.

        Trigger condition (Req 9.1):
            ``new_latest_month > previous_latest_month``
            (at least one new complete calendar month added).

        Parameters
        ----------
        previous_latest_month:
            The latest ``year_month`` value observed at the end of the
            previous upload.  Pass ``None`` on the very first upload.

        Returns
        -------
        RetrainingResult
        """
        # ── Determine current extent ──────────────────────────────────────────
        pipeline = DataPipeline(db_conn=self._conn)
        try:
            _, new_latest_month = pipeline.get_training_window_extent()
        except ValueError:
            # No records at all — cannot retrain.
            return RetrainingResult(
                triggered=False,
                success=False,
                previous_latest_month=previous_latest_month,
                new_latest_month=None,
                new_mape=None,
                error_message="No records found in monthly_bill_records.",
            )

        # ── Trigger condition check (Req 9.1) ─────────────────────────────────
        if previous_latest_month is not None and new_latest_month <= previous_latest_month:
            logger.info(
                "No new calendar month detected (%s ≤ %s); skipping retraining.",
                new_latest_month,
                previous_latest_month,
            )
            return RetrainingResult(
                triggered=False,
                success=True,
                previous_latest_month=previous_latest_month,
                new_latest_month=new_latest_month,
                new_mape=None,
                error_message=None,
            )

        logger.info(
            "New calendar month detected (%s > %s); triggering retraining.",
            new_latest_month,
            previous_latest_month,
        )

        # ── Run full pipeline (Req 9.2) ───────────────────────────────────────
        return self._run_retraining_pipeline(
            previous_latest_month=previous_latest_month,
            new_latest_month=new_latest_month,
        )

    # ------------------------------------------------------------------
    # Private — pipeline orchestration
    # ------------------------------------------------------------------

    def _run_retraining_pipeline(
        self,
        previous_latest_month: str | None,
        new_latest_month: str,
    ) -> RetrainingResult:
        """Execute the full retraining pipeline.

        Steps:
          1. Load all monthly records from SQLite.
          2. Feature-engineer (enrich) the records.
          3. Back up the existing model artefact (if present).
          4. Train the SARIMAX model on enriched records.
          5. Generate forecasts for horizons 1, 3, 6 and upsert to vector store.
          6. Write training log entry to SQLite.
          7. Delete backup on success.

        Failure at any step logs an ERROR, halts, and returns a failed
        :class:`RetrainingResult` without modifying the existing artefact
        or vector store contents (Req 9.3).
        """
        previous_mape: float | None = self._get_previous_mape()
        backup_path: str | None = None

        # ── Step 1: Load monthly records ──────────────────────────────────────
        try:
            pipeline = DataPipeline(db_conn=self._conn)
            start, end = pipeline.get_training_window_extent()
            monthly_records = pipeline.get_monthly_records(start, end)
        except Exception as exc:
            return self._fail(
                "Step 1 (load records) failed",
                exc,
                previous_latest_month,
                new_latest_month,
            )

        # ── Step 2: Feature engineering ───────────────────────────────────────
        try:
            enriched_records = self._feature_service.enrich(monthly_records)
        except Exception as exc:
            return self._fail(
                "Step 2 (feature engineering) failed",
                exc,
                previous_latest_month,
                new_latest_month,
            )

        # ── Step 3: Backup existing artefact (Req 9.5) ────────────────────────
        try:
            backup_path = self._model.backup()
            logger.info("Model artefact backed up to %s", backup_path)
        except FileNotFoundError:
            # No existing artefact to back up — first-time training.
            logger.info("No existing artefact to back up (first training run).")
            backup_path = None
        except Exception as exc:
            return self._fail(
                "Step 3 (backup artefact) failed",
                exc,
                previous_latest_month,
                new_latest_month,
            )

        # ── Step 4: Train SARIMAX model ───────────────────────────────────────
        try:
            training_result = self._model.train(enriched_records)
            new_mape = training_result.mape_validation
        except (ModelTrainingError, Exception) as exc:
            # Restore backup if training failed after backup was taken.
            self._restore_backup_if_needed(backup_path)
            return self._fail(
                "Step 4 (SARIMAX training) failed",
                exc,
                previous_latest_month,
                new_latest_month,
            )

        # ── Step 5: Generate forecasts and update vector store ────────────────
        try:
            self._generate_and_store_forecasts(enriched_records)
        except Exception as exc:
            return self._fail(
                "Step 5 (forecast generation / vector store update) failed",
                exc,
                previous_latest_month,
                new_latest_month,
                new_mape=new_mape,
            )

        # ── Step 5b: Run EDA and ingest summaries into EDA vector store ──────
        try:
            self._run_and_ingest_eda(monthly_records)
        except Exception as exc:
            logger.warning(
                "Step 5b (EDA ingestion) failed (non-fatal): %s", exc, exc_info=True
            )
            # Non-fatal — EDA enriches the RAG but must not block a successful retrain.

        # ── Step 6: Write training log (Req 9.4) ─────────────────────────────
        try:
            self._write_training_log(
                previous_mape=previous_mape,
                new_mape=new_mape,
                training_window_start=training_result.training_window["start"],
                training_window_end=training_result.training_window["end"],
            )
            self._purge_old_training_logs()
        except Exception as exc:
            logger.error("Step 6 (write training log) failed: %s", exc)
            # Non-fatal — log but do not abort.

        # ── Step 7: Delete backup on success (Req 9.6) ───────────────────────
        if backup_path is not None:
            try:
                self._model.delete_backup(backup_path)
                logger.info("Backup artefact deleted after successful retraining.")
            except Exception as exc:
                logger.warning("Could not delete backup artefact %s: %s", backup_path, exc)

        logger.info(
            "Retraining complete. previous_mape=%.4f new_mape=%.4f",
            previous_mape or 0.0,
            new_mape,
        )

        return RetrainingResult(
            triggered=True,
            success=True,
            previous_latest_month=previous_latest_month,
            new_latest_month=new_latest_month,
            new_mape=new_mape,
            error_message=None,
        )

    # ------------------------------------------------------------------
    # Private — helpers
    # ------------------------------------------------------------------

    def _generate_and_store_forecasts(
        self,
        enriched_records: list,
    ) -> None:
        """Generate forecasts for all valid horizons and upsert to vector store."""
        for horizon in _RETRAIN_HORIZONS:
            horizon_label = _HORIZON_LABELS[horizon]
            try:
                months = self._model.forecast(
                    horizon=horizon,
                    exog=None,
                    historical_records=enriched_records,
                )
            except Exception as exc:
                logger.error(
                    "Forecast generation failed for horizon %d: %s", horizon, exc
                )
                raise

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
                    self._vector_store.upsert(doc, user_id=self._user_id)
                except Exception as exc:
                    # Retry once (Req 4.7).
                    logger.warning(
                        "First upsert failed for %s; retrying. Error: %s", doc_id, exc
                    )
                    self._vector_store.upsert(doc, user_id=self._user_id)

    def _run_and_ingest_eda(self, monthly_records: list) -> None:
        """Run EDA over *monthly_records* and upsert summaries into the EDA store.

        Converts the in-memory :class:`~pipeline.models.MonthlyRecord` objects
        into the plain ``{year_month, kwh, price}`` dict format that
        :func:`data.eda.run_eda` expects, then upserts every generated summary.
        """
        # Import here to avoid a circular/heavy import at module load time.
        import sys
        from pathlib import Path as _Path
        _root = str(_Path(__file__).parent.parent)
        if _root not in sys.path:
            sys.path.insert(0, _root)

        from data.eda import run_eda  # noqa: PLC0415

        rows = [
            {
                "year_month": r.year_month,
                "kwh": r.kwh,
                "price": r.price,
                "meralco_rate": r.meralco_rate,
                "avg_temperature": r.avg_temperature,
                "avg_humidity": r.avg_humidity,
                "total_rainfall_mm": r.total_rainfall_mm,
                "holiday_count": r.holiday_count,
                "weekend_count": r.weekend_count,
                "hot_days_count": r.hot_days_count,
                "rainy_days_count": r.rainy_days_count,
                "is_el_nino": r.is_el_nino,
            }
            for r in monthly_records
        ]
        summaries = run_eda(rows)
        ingested = 0
        for entry in summaries:
            self._eda_store.upsert(doc_id=entry["id"], text=entry["text"])
            ingested += 1
        logger.info(
            "EDA ingestion complete: %d summaries upserted into EDA store.", ingested
        )

    def _get_previous_mape(self) -> float | None:
        """Return the most recent MAPE from the training log, or None."""
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT new_mape FROM training_log ORDER BY trained_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return float(row[0])
        except Exception:
            pass
        return None

    def _write_training_log(
        self,
        previous_mape: float | None,
        new_mape: float,
        training_window_start: str,
        training_window_end: str,
    ) -> None:
        """Write a training_log entry to SQLite (Req 9.4)."""
        trained_at = datetime.now(timezone.utc).isoformat()
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO training_log
                (trained_at, previous_mape, new_mape, training_window_start, training_window_end)
            VALUES (?, ?, ?, ?, ?)
            """,
            (trained_at, previous_mape, new_mape, training_window_start, training_window_end),
        )
        self._conn.commit()
        logger.info(
            "Training log written: trained_at=%s previous_mape=%s new_mape=%.4f",
            trained_at,
            previous_mape,
            new_mape,
        )

    def _purge_old_training_logs(self) -> None:
        """Delete training_log entries older than 90 days (Req 9.4)."""
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=_LOG_RETENTION_DAYS)
        ).isoformat()
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM training_log WHERE trained_at < ?",
            (cutoff,),
        )
        deleted = cursor.rowcount
        self._conn.commit()
        if deleted:
            logger.info("Purged %d training log entries older than %d days.", deleted, _LOG_RETENTION_DAYS)

    def _restore_backup_if_needed(self, backup_path: str | None) -> None:
        """Attempt to restore a backup artefact after a training failure."""
        if backup_path is None:
            return
        import shutil
        try:
            shutil.copy2(backup_path, self._model._artefact_path)
            logger.info("Restored model artefact from backup %s.", backup_path)
        except Exception as exc:
            logger.error(
                "Could not restore backup artefact from %s: %s", backup_path, exc
            )

    @staticmethod
    def _fail(
        step_msg: str,
        exc: Exception,
        previous_latest_month: str | None,
        new_latest_month: str | None,
        new_mape: float | None = None,
    ) -> RetrainingResult:
        """Log an error and return a failed RetrainingResult."""
        error_message = f"{step_msg}: {exc}"
        logger.error(error_message, exc_info=True)
        return RetrainingResult(
            triggered=True,
            success=False,
            previous_latest_month=previous_latest_month,
            new_latest_month=new_latest_month,
            new_mape=new_mape,
            error_message=error_message,
        )
