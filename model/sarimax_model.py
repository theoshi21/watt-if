"""
SARIMAX Model for WATT-IF.

Trains a single SARIMAX model on monthly kWh consumption.
Price is derived post-forecast as:  predicted_price = predicted_kwh × meralco_rate

Exogenous variables (9 columns):
  meralco_rate, avg_temperature, avg_humidity, total_rainfall_mm,
  holiday_count, weekend_count, hot_days_count, rainy_days_count, is_el_nino

Training uses an 80/10/10 chronological split:
  - 80% train     — fit via auto_arima + SARIMAX
  - 10% validation — compute MAPE
  - 10% test       — held out
"""

from __future__ import annotations

import calendar
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pmdarima as pm

from pipeline.models import (
    EnrichedRecord,
    ExogenousRow,
    ForecastMonth,
    ModelTrainingError,
    TrainingResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MIN_RECORDS = 14
_SEASONAL_PERIOD = 12
_MAPE_WARNING_THRESHOLD = 0.30

_DEFAULT_ARTEFACT_DIR = Path(__file__).parent.parent / "data"
_DEFAULT_ARTEFACT_PATH = _DEFAULT_ARTEFACT_DIR / "sarimax_model.joblib"

# New 9-column exogenous set
_EXOG_COLUMNS: list[str] = [
    "meralco_rate",
    "avg_temperature",
    "avg_humidity",
    "total_rainfall_mm",
    "holiday_count",
    "weekend_count",
    "hot_days_count",
    "rainy_days_count",
    "is_el_nino",
]

_VALID_HORIZONS: frozenset[int] = frozenset({1, 3, 6})
_HORIZON_LABELS: dict[int, str] = {1: "1m", 3: "3m", 6: "6m"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    nonzero = actual != 0.0
    if not nonzero.any():
        return 0.0
    return float(np.mean(np.abs((actual[nonzero] - predicted[nonzero]) / actual[nonzero])))


def _next_year_month(year_month: str, offset: int) -> str:
    year, month = int(year_month[:4]), int(year_month[5:7])
    total_months = year * 12 + (month - 1) + offset
    new_year, new_month = divmod(total_months, 12)
    return f"{new_year:04d}-{new_month + 1:02d}"


def _records_to_frame(records: list[EnrichedRecord]) -> pd.DataFrame:
    rows = [
        {
            "year_month": r.year_month,
            "kwh": r.kwh,
            "price": r.price,
            "meralco_rate": r.meralco_rate,
            "avg_temperature": r.avg_temperature,
            "avg_humidity": r.avg_humidity,
            "total_rainfall_mm": r.total_rainfall_mm,
            "holiday_count": float(r.holiday_count),
            "weekend_count": float(r.weekend_count),
            "hot_days_count": float(r.hot_days_count),
            "rainy_days_count": float(r.rainy_days_count),
            "is_el_nino": float(r.is_el_nino),
        }
        for r in records
    ]
    df = pd.DataFrame(rows).sort_values("year_month").reset_index(drop=True)
    return df


def _exog_rows_to_frame(exog: list[ExogenousRow]) -> pd.DataFrame:
    rows = [
        {
            "meralco_rate": r.meralco_rate,
            "avg_temperature": r.avg_temperature,
            "avg_humidity": r.avg_humidity,
            "total_rainfall_mm": r.total_rainfall_mm,
            "holiday_count": float(r.holiday_count),
            "weekend_count": float(r.weekend_count),
            "hot_days_count": float(r.hot_days_count),
            "rainy_days_count": float(r.rainy_days_count),
            "is_el_nino": float(r.is_el_nino),
        }
        for r in exog
    ]
    return pd.DataFrame(rows)[_EXOG_COLUMNS]


# ---------------------------------------------------------------------------
# SARIMAXModel
# ---------------------------------------------------------------------------

class SARIMAXModel:
    """Trains a single SARIMAX kWh model; derives price from Meralco rate."""

    def __init__(self, artefact_path: str | Path = _DEFAULT_ARTEFACT_PATH) -> None:
        self._artefact_path = Path(artefact_path)
        self._artefact: dict | None = None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, records: list[EnrichedRecord]) -> TrainingResult:
        """Train SARIMAX on kWh with the 9 new exogenous variables."""
        n = len(records)
        if n < _MIN_RECORDS:
            msg = (
                f"Insufficient data: {n} records; "
                f"at least {_MIN_RECORDS} required."
            )
            logger.error(msg)
            raise ModelTrainingError(msg)

        df = _records_to_frame(records)

        train_end = int(n * 0.80)
        val_end = min(train_end + max(1, int(n * 0.10)), n - 1)

        df_train = df.iloc[:train_end]
        df_val   = df.iloc[train_end:val_end]

        y_train = df_train["kwh"].values
        y_val   = df_val["kwh"].values
        exog_train = df_train[_EXOG_COLUMNS].values
        exog_val   = df_val[_EXOG_COLUMNS].values

        training_window = {
            "start": df_train["year_month"].iloc[0],
            "end":   df_train["year_month"].iloc[-1],
        }

        # ── auto_arima ────────────────────────────────────────────────────────
        n_train = len(df_train)
        use_seasonal = n_train >= 2 * _SEASONAL_PERIOD
        if not use_seasonal:
            logger.warning(
                "Training set has only %d records (< 2*m=%d); "
                "seasonal component disabled.",
                n_train, 2 * _SEASONAL_PERIOD,
            )

        logger.info(
            "Running auto_arima on %d training records (seasonal=%s, m=%d)…",
            n_train, use_seasonal, _SEASONAL_PERIOD,
        )
        try:
            auto_result = pm.auto_arima(
                y_train,
                X=exog_train,
                seasonal=use_seasonal,
                m=_SEASONAL_PERIOD if use_seasonal else 1,
                seasonal_test="ch",
                information_criterion="aic",
                stepwise=True,
                suppress_warnings=True,
                error_action="raise",
                trace=False,
            )
        except Exception as exc:
            msg = f"auto_arima failed to converge: {exc}"
            logger.error(msg)
            raise ModelTrainingError(msg) from exc

        order = auto_result.order
        _raw_s = auto_result.seasonal_order
        seasonal_order = (_raw_s[0], _raw_s[1], _raw_s[2], _SEASONAL_PERIOD)

        logger.info("auto_arima: order=%s seasonal_order=%s", order, seasonal_order)

        # ── Validation MAPE ───────────────────────────────────────────────────
        mape_kwh = 0.0
        if len(df_val) > 0:
            try:
                pred_kwh = auto_result.predict(n_periods=len(df_val), X=exog_val)
                mape_kwh = _compute_mape(y_val, pred_kwh)
            except Exception as exc:
                logger.warning("Could not compute validation MAPE: %s", exc)

        mape_validation = mape_kwh
        logger.info("Validation MAPE — kWh: %.2f%%", mape_kwh * 100)

        if mape_validation > _MAPE_WARNING_THRESHOLD:
            logger.warning(
                "Model accuracy below threshold: MAPE = %.2f%% (threshold = %.0f%%)",
                mape_validation * 100, _MAPE_WARNING_THRESHOLD * 100,
            )

        # ── Persist artefact ──────────────────────────────────────────────────
        trained_at = datetime.now(timezone.utc).isoformat()
        artefact = {
            "model_kwh": auto_result,
            "order": order,
            "seasonal_order": seasonal_order,
            "exog_columns": _EXOG_COLUMNS,
            "trained_at": trained_at,
            "mape_kwh": mape_kwh,
            "mape_price": None,     # price is derived, not modelled
            "mape_validation": mape_validation,
            "training_window": training_window,
        }

        self._artefact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(artefact, self._artefact_path)
        self._artefact = artefact

        logger.info("SARIMAX artefact saved to %s", self._artefact_path)

        return TrainingResult(
            order=order,
            seasonal_order=seasonal_order,
            mape_validation=mape_validation,
            training_window=training_window,
            artefact_path=str(self._artefact_path),
        )

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(self, path: str | Path | None = None) -> None:
        load_path = Path(path) if path is not None else self._artefact_path
        if not load_path.exists():
            raise FileNotFoundError(
                f"SARIMAX artefact not found at {load_path}. Train the model first."
            )
        self._artefact = joblib.load(load_path)
        logger.info("SARIMAX artefact loaded from %s", load_path)

    # ------------------------------------------------------------------
    # Forecasting
    # ------------------------------------------------------------------

    def forecast(
        self,
        horizon: int,
        exog: list[ExogenousRow] | None = None,
        historical_records: list[EnrichedRecord] | None = None,
    ) -> list[ForecastMonth]:
        """Generate kWh forecasts; derive price as kwh × meralco_rate."""
        if horizon not in _VALID_HORIZONS:
            raise ValueError(f"Invalid horizon {horizon!r}: must be one of {sorted(_VALID_HORIZONS)}.")
        if self._artefact is None:
            raise ValueError("No SARIMAX artefact loaded. Call load() or train() first.")
        if historical_records is not None and len(historical_records) < _MIN_RECORDS:
            raise ValueError(
                f"Insufficient historical data: {len(historical_records)} records; "
                f"at least {_MIN_RECORDS} required."
            )

        model_kwh = self._artefact["model_kwh"]
        training_window = self._artefact["training_window"]

        # Resolve exogenous
        if exog is None:
            exog_array, exog_rows = self._compute_fallback_exog(horizon, historical_records)
        else:
            if len(exog) != horizon:
                raise ValueError(
                    f"Expected {horizon} ExogenousRow(s), got {len(exog)}."
                )
            exog_array = _exog_rows_to_frame(exog).values
            exog_rows = exog

        # Generate kWh forecast + 95% CI
        try:
            fc_kwh, ci_kwh = model_kwh.predict(
                n_periods=horizon, X=exog_array,
                return_conf_int=True, alpha=0.05
            )
        except Exception as exc:
            raise ValueError(f"Forecast generation failed: {exc}") from exc

        last_month = training_window["end"]
        results: list[ForecastMonth] = []

        for i in range(horizon):
            ym = _next_year_month(last_month, i + 1)
            kwh = max(0.0, float(fc_kwh[i]))
            kwh_lo = max(0.0, float(ci_kwh[i][0]))
            kwh_hi = max(0.0, float(ci_kwh[i][1]))

            # Derive price from Meralco rate
            rate = float(exog_rows[i].meralco_rate) if isinstance(exog_rows[i], ExogenousRow) \
                   else float(exog_rows[i]["meralco_rate"])
            price = max(0.0, kwh * rate)
            price_lo = max(0.0, kwh_lo * rate)
            price_hi = max(0.0, kwh_hi * rate)

            ex = exog_rows[i]
            if isinstance(ex, ExogenousRow):
                avg_temp = ex.avg_temperature
                avg_hum = ex.avg_humidity
                rainfall = ex.total_rainfall_mm
                holidays = ex.holiday_count
                weekends = ex.weekend_count
                hot_days = ex.hot_days_count
                rainy_days = ex.rainy_days_count
                el_nino = ex.is_el_nino
            else:
                avg_temp = ex["avg_temperature"]
                avg_hum = ex["avg_humidity"]
                rainfall = ex["total_rainfall_mm"]
                holidays = ex["holiday_count"]
                weekends = ex["weekend_count"]
                hot_days = ex["hot_days_count"]
                rainy_days = ex["rainy_days_count"]
                el_nino = ex["is_el_nino"]

            results.append(ForecastMonth(
                year_month=ym,
                kwh_forecast=kwh,
                kwh_lower_95=kwh_lo,
                kwh_upper_95=kwh_hi,
                price_forecast=price,
                price_lower_95=price_lo,
                price_upper_95=price_hi,
                meralco_rate=rate,
                avg_temperature=avg_temp,
                avg_humidity=avg_hum,
                total_rainfall_mm=rainfall,
                holiday_count=int(holidays),
                weekend_count=int(weekends),
                hot_days_count=int(hot_days),
                rainy_days_count=int(rainy_days),
                is_el_nino=int(el_nino),
            ))

        return results

    # ------------------------------------------------------------------
    # Backup / restore
    # ------------------------------------------------------------------

    def backup(self) -> str:
        if not self._artefact_path.exists():
            raise FileNotFoundError(f"Cannot backup: no artefact at {self._artefact_path}.")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = self._artefact_path.parent / (
            f"{self._artefact_path.stem}.backup_{timestamp}{self._artefact_path.suffix}"
        )
        shutil.copy2(self._artefact_path, backup_path)
        logger.info("Artefact backed up to %s", backup_path)
        return str(backup_path)

    def delete_backup(self, backup_path: str | Path) -> None:
        path = Path(backup_path)
        if path.exists():
            path.unlink()
            logger.info("Backup deleted: %s", path)
        else:
            logger.warning("delete_backup: file not found: %s", path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_fallback_exog(
        self,
        horizon: int,
        historical_records: list[EnrichedRecord] | None,
    ) -> tuple[np.ndarray, list[dict]]:
        """Return (exog_array, list_of_dicts) using month-aware seasonality.

        Instead of a flat global mean (which collapses to 0.0 when there are
        no historical records and causes SARIMAX to forecast 0), we estimate
        each future month's exogenous values from the same calendar-month
        observations in the historical data.  For ``meralco_rate`` we also
        apply a simple recent-trend extrapolation so slowly-rising rates are
        projected forward.

        Fallback hierarchy (most to least preferred):
          1. Same-calendar-month historical mean (month-level seasonality)
          2. Global historical mean (all months average)
          3. Philippine climate / calendar defaults (no historical data at all)
        """
        logger.warning(
            "Using historical-mean fallback exogenous values for forecast "
            "(no explicit exog supplied)."
        )

        # ── Log diagnostic info ───────────────────────────────────────────────
        n_hist = len(historical_records) if historical_records else 0
        logger.info(
            "[fallback_exog] historical_records length: %d", n_hist
        )

        training_window = self._artefact["training_window"] if self._artefact else {}
        last_month = training_window.get("end", "2024-12")

        # Build a lookup: calendar month (1–12) → list of historical records
        by_month: dict[int, list[EnrichedRecord]] = {m: [] for m in range(1, 13)}

        # Global means as a safety net
        global_defaults: dict[str, float] = {
            "meralco_rate": 11.8,        # typical Meralco residential ~₱11–12/kWh
            "avg_temperature": 28.5,     # Philippine annual mean
            "avg_humidity": 78.0,
            "total_rainfall_mm": 150.0,
            "holiday_count": 2.0,
            "weekend_count": 8.0,        # ~8 weekend days/month
            "hot_days_count": 10.0,
            "rainy_days_count": 8.0,
            "is_el_nino": 0.0,
        }

        if historical_records:
            df = _records_to_frame(historical_records)

            logger.info(
                "[fallback_exog] dataframe columns: %s", list(df.columns)
            )
            logger.info(
                "[fallback_exog] dataframe shape: %s", df.shape
            )

            # Log per-column means
            for col in _EXOG_COLUMNS:
                if col in df.columns:
                    col_mean = float(df[col].mean())
                    logger.info(
                        "[fallback_exog] column '%s' mean: %.4f (non-zero: %d/%d)",
                        col,
                        col_mean,
                        int((df[col] != 0).sum()),
                        len(df),
                    )
                else:
                    logger.warning("[fallback_exog] column '%s' MISSING from dataframe", col)

            # Populate global defaults from actual data
            for col in _EXOG_COLUMNS:
                if col in df.columns:
                    m = float(df[col].mean())
                    if not np.isnan(m):
                        global_defaults[col] = m

            # Populate per-calendar-month lookup
            for r in historical_records:
                try:
                    cal_month = int(r.year_month[5:7])
                    by_month[cal_month].append(r)
                except (ValueError, IndexError):
                    pass

            # ── Meralco rate trend: use most recent 6 months slope ────────────
            if len(df) >= 2:
                recent = df.tail(min(6, len(df)))
                x = np.arange(len(recent))
                y = recent["meralco_rate"].values.astype(float)
                if np.std(y) > 0:
                    slope = float(np.polyfit(x, y, 1)[0])
                else:
                    slope = 0.0
                # Cap at ±0.05 ₱/month to avoid wild extrapolation
                slope = max(-0.05, min(0.05, slope))
                global_defaults["_rate_slope"] = slope
                global_defaults["_rate_base"] = float(recent["meralco_rate"].iloc[-1])
                logger.info(
                    "[fallback_exog] meralco_rate trend: base=%.4f slope=%.5f/month",
                    global_defaults["_rate_base"],
                    slope,
                )
            else:
                global_defaults["_rate_slope"] = 0.0
                global_defaults["_rate_base"] = global_defaults["meralco_rate"]

        else:
            logger.warning(
                "[fallback_exog] No historical records provided — "
                "using Philippine climate/calendar defaults for all months."
            )
            global_defaults["_rate_slope"] = 0.0
            global_defaults["_rate_base"] = global_defaults["meralco_rate"]

        # ── Philippine monthly climate prior (no-data safety net) ─────────────
        # Source: PAGASA monthly normals for Metro Manila / national average
        _ph_temp:     dict[int, float] = {1: 26.0, 2: 26.5, 3: 28.0, 4: 29.5, 5: 29.5,
                                           6: 28.5, 7: 27.5, 8: 27.5, 9: 27.5, 10: 27.5,
                                           11: 27.0, 12: 26.5}
        _ph_hum:      dict[int, float] = {1: 78, 2: 76, 3: 74, 4: 74, 5: 78,
                                           6: 82, 7: 85, 8: 85, 9: 84, 10: 82,
                                           11: 80, 12: 79}
        _ph_rain:     dict[int, float] = {1: 20,  2: 15,  3: 20,  4: 35,  5: 130,
                                           6: 250, 7: 320, 8: 350, 9: 300, 10: 200,
                                          11: 100, 12: 50}
        _ph_hot_days: dict[int, float] = {1: 4,  2: 5,  3: 12, 4: 18, 5: 17,
                                           6: 10, 7: 6,  8: 6,  9: 7,  10: 8,
                                          11: 7,  12: 5}
        _ph_rainy_days: dict[int, float] = {1: 5,  2: 4,  3: 5,  4: 7,  5: 14,
                                             6: 20, 7: 24, 8: 23, 9: 22, 10: 18,
                                            11: 13, 12: 9}
        # PH public holiday count per month (regular + special, approximate)
        _ph_holidays: dict[int, int] = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2,
                                         6: 2, 7: 1, 8: 2, 9: 1, 10: 1,
                                        11: 2, 12: 4}

        # ── Build one dict per future month ───────────────────────────────────
        rows: list[dict] = []
        rate_slope = global_defaults.get("_rate_slope", 0.0)
        rate_base  = global_defaults.get("_rate_base",  global_defaults["meralco_rate"])

        for i in range(horizon):
            ym = _next_year_month(last_month, i + 1)
            try:
                cal_month = int(ym[5:7])
                cal_year  = int(ym[:4])
            except (ValueError, IndexError):
                cal_month = 1
                cal_year  = datetime.now().year

            same_month_records = by_month.get(cal_month, [])

            def _hist_mean(attr: str, default: float) -> float:
                """Mean of *attr* over same-calendar-month records, else *default*."""
                vals = []
                for rec in same_month_records:
                    v = getattr(rec, attr, None)
                    if v is not None:
                        vals.append(float(v))
                if vals:
                    return float(np.mean(vals))
                # No same-month data → fall back to global historical mean
                gv = global_defaults.get(attr, default)
                return float(gv) if not np.isnan(float(gv)) else default

            # ── Meralco rate: trend-projected, month-agnostic ─────────────────
            projected_rate = rate_base + rate_slope * (i + 1)
            # If same-month history exists, blend trend projection with it
            if same_month_records:
                same_month_rate = _hist_mean("meralco_rate", projected_rate)
                # Weight recent trend more (60%) vs same-month average (40%)
                projected_rate = 0.6 * projected_rate + 0.4 * same_month_rate
            projected_rate = max(5.0, projected_rate)  # floor at ₱5/kWh

            # ── Weekend count from real calendar ──────────────────────────────
            try:
                _, days_in_month = calendar.monthrange(cal_year, cal_month)
                weekend_days = sum(
                    1 for d in range(1, days_in_month + 1)
                    if datetime(cal_year, cal_month, d).weekday() >= 5
                )
            except Exception:
                weekend_days = 8

            # ── All other variables: same-calendar-month seasonality ──────────
            row = {
                "meralco_rate":      projected_rate,
                "avg_temperature":   _hist_mean("avg_temperature",   _ph_temp[cal_month]),
                "avg_humidity":      _hist_mean("avg_humidity",      _ph_hum[cal_month]),
                "total_rainfall_mm": _hist_mean("total_rainfall_mm", _ph_rain[cal_month]),
                "holiday_count":     float(round(_hist_mean("holiday_count",   float(_ph_holidays[cal_month])))),
                "weekend_count":     float(weekend_days),
                "hot_days_count":    float(round(_hist_mean("hot_days_count",  _ph_hot_days[cal_month]))),
                "rainy_days_count":  float(round(_hist_mean("rainy_days_count", _ph_rainy_days[cal_month]))),
                "is_el_nino":        float(round(_hist_mean("is_el_nino",       0.0))),
            }
            rows.append(row)

            logger.info(
                "[fallback_exog] %s (cal_month=%d, same_month_records=%d): "
                "rate=%.4f temp=%.1f hum=%.1f rain=%.1f holidays=%d weekends=%d "
                "hot_days=%d rainy_days=%d el_nino=%d",
                ym, cal_month, len(same_month_records),
                row["meralco_rate"], row["avg_temperature"], row["avg_humidity"],
                row["total_rainfall_mm"], int(row["holiday_count"]),
                int(row["weekend_count"]), int(row["hot_days_count"]),
                int(row["rainy_days_count"]), int(row["is_el_nino"]),
            )

        array = np.array([[r[col] for col in _EXOG_COLUMNS] for r in rows], dtype=float)

        logger.info(
            "[fallback_exog] exog_array shape: %s\n%s",
            array.shape,
            np.array2string(array, precision=4, suppress_small=True),
        )

        return array, rows
