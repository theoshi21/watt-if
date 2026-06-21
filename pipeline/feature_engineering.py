"""
Feature Engineering Service for WATT-IF.

With the new dataset, all exogenous variables (temperature, humidity, rainfall,
Meralco rate, holiday count, etc.) are already present in the uploaded CSV.
This service simply converts MonthlyRecord objects into EnrichedRecord objects
without any external API calls.

For the forecast horizon, fallback values are computed using month-level
seasonality from historical data (same calendar month averages) rather than
flat global means to avoid producing all-zero exogenous inputs.
"""

from __future__ import annotations

import calendar
import logging
from datetime import datetime

import numpy as np

from pipeline.models import EnrichedRecord, ExogenousRow, MonthlyRecord

logger = logging.getLogger(__name__)

# ── Philippine monthly climate priors (PAGASA Metro Manila normals) ───────────
# Used when no historical data exists for a given calendar month.
_PH_TEMP:       dict[int, float] = {1: 26.0, 2: 26.5, 3: 28.0, 4: 29.5, 5: 29.5,
                                     6: 28.5, 7: 27.5, 8: 27.5, 9: 27.5, 10: 27.5,
                                    11: 27.0, 12: 26.5}
_PH_HUM:        dict[int, float] = {1: 78, 2: 76, 3: 74, 4: 74, 5: 78,
                                     6: 82, 7: 85, 8: 85, 9: 84, 10: 82,
                                    11: 80, 12: 79}
_PH_RAIN:       dict[int, float] = {1: 20,  2: 15,  3: 20,  4: 35,  5: 130,
                                     6: 250, 7: 320, 8: 350, 9: 300, 10: 200,
                                    11: 100, 12: 50}
_PH_HOT_DAYS:   dict[int, float] = {1: 4,  2: 5,  3: 12, 4: 18, 5: 17,
                                     6: 10, 7: 6,  8: 6,  9: 7,  10: 8,
                                    11: 7,  12: 5}
_PH_RAINY_DAYS: dict[int, float] = {1: 5,  2: 4,  3: 5,  4: 7,  5: 14,
                                     6: 20, 7: 24, 8: 23, 9: 22, 10: 18,
                                    11: 13, 12: 9}
_PH_HOLIDAYS:   dict[int, int]   = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2,
                                     6: 2, 7: 1, 8: 2, 9: 1, 10: 1,
                                    11: 2, 12: 4}
_PH_MERALCO_RATE: float = 11.8   # ₱/kWh typical residential rate


class FeatureEngineeringService:
    """Pass-through enrichment: promotes MonthlyRecord → EnrichedRecord.

    All exogenous fields are already present on MonthlyRecord from the new
    dataset. This class exists to preserve the existing interface used by
    RetrainingService and the SARIMAX model.
    """

    def enrich(self, records: list[MonthlyRecord]) -> list[EnrichedRecord]:
        """Convert MonthlyRecord list to EnrichedRecord list."""
        return [
            EnrichedRecord(
                year_month=r.year_month,
                kwh=r.kwh,
                price=r.price,
                meralco_rate=r.meralco_rate,
                avg_temperature=r.avg_temperature,
                avg_humidity=r.avg_humidity,
                total_rainfall_mm=r.total_rainfall_mm,
                holiday_count=int(r.holiday_count),
                weekend_count=int(r.weekend_count),
                hot_days_count=int(r.hot_days_count),
                rainy_days_count=int(r.rainy_days_count),
                is_el_nino=int(r.is_el_nino),
            )
            for r in records
        ]

    def enrich_forecast_horizon(
        self,
        months: list[str],
        historical_records: list[EnrichedRecord] | None = None,
    ) -> list[ExogenousRow]:
        """Build ExogenousRow values for future forecast months.

        Uses same-calendar-month historical means (seasonality) rather than
        global means so that forecasts receive realistic, non-zero exogenous
        inputs.  Falls back to Philippine climate/calendar priors when no
        historical data exists for a given month.

        Parameters
        ----------
        months:
            List of YYYY-MM strings for forecast months.
        historical_records:
            Historical enriched records used to compute seasonal means.
        """
        # ── Build calendar-month lookup ───────────────────────────────────────
        by_month: dict[int, list[EnrichedRecord]] = {m: [] for m in range(1, 13)}
        if historical_records:
            for r in historical_records:
                try:
                    cal_m = int(r.year_month[5:7])
                    by_month[cal_m].append(r)
                except (ValueError, IndexError):
                    pass

        # ── Meralco rate trend (last 6 months slope) ──────────────────────────
        rate_base = _PH_MERALCO_RATE
        rate_slope = 0.0
        if historical_records:
            rates = [r.meralco_rate for r in historical_records[-6:]]
            if rates:
                rate_base = float(rates[-1])
            if len(rates) >= 2:
                x = np.arange(len(rates), dtype=float)
                y = np.array(rates, dtype=float)
                if np.std(y) > 0:
                    rate_slope = float(np.polyfit(x, y, 1)[0])
                rate_slope = max(-0.05, min(0.05, rate_slope))

        logger.info(
            "enrich_forecast_horizon: %d months, %d historical records, "
            "rate_base=%.4f rate_slope=%.5f/month",
            len(months),
            len(historical_records) if historical_records else 0,
            rate_base,
            rate_slope,
        )

        results: list[ExogenousRow] = []
        for i, ym in enumerate(months):
            try:
                cal_month = int(ym[5:7])
                cal_year  = int(ym[:4])
            except (ValueError, IndexError):
                cal_month = 1
                cal_year  = datetime.now().year

            same = by_month.get(cal_month, [])

            def _mean(attr: str, default: float) -> float:
                vals = [float(getattr(r, attr)) for r in same if getattr(r, attr, None) is not None]
                if vals:
                    return float(np.mean(vals))
                if historical_records:
                    all_vals = [float(getattr(r, attr)) for r in historical_records
                                if getattr(r, attr, None) is not None]
                    if all_vals:
                        return float(np.mean(all_vals))
                return default

            # Real calendar weekend count
            try:
                _, days = calendar.monthrange(cal_year, cal_month)
                weekends = sum(
                    1 for d in range(1, days + 1)
                    if datetime(cal_year, cal_month, d).weekday() >= 5
                )
            except Exception:
                weekends = 8

            # Projected Meralco rate
            projected_rate = rate_base + rate_slope * (i + 1)
            if same:
                same_rate = _mean("meralco_rate", projected_rate)
                projected_rate = 0.6 * projected_rate + 0.4 * same_rate
            projected_rate = max(5.0, projected_rate)

            row = ExogenousRow(
                year_month=ym,
                meralco_rate=projected_rate,
                avg_temperature=_mean("avg_temperature",   _PH_TEMP[cal_month]),
                avg_humidity=_mean("avg_humidity",         _PH_HUM[cal_month]),
                total_rainfall_mm=_mean("total_rainfall_mm", _PH_RAIN[cal_month]),
                holiday_count=int(round(_mean("holiday_count",   float(_PH_HOLIDAYS[cal_month])))),
                weekend_count=int(weekends),
                hot_days_count=int(round(_mean("hot_days_count",   _PH_HOT_DAYS[cal_month]))),
                rainy_days_count=int(round(_mean("rainy_days_count", _PH_RAINY_DAYS[cal_month]))),
                is_el_nino=int(round(_mean("is_el_nino", 0.0))),
            )
            results.append(row)

            logger.info(
                "enrich_forecast_horizon[%d] %s: rate=%.4f temp=%.1f hum=%.1f "
                "rain=%.1f holidays=%d weekends=%d hot=%d rainy=%d el_nino=%d",
                i, ym,
                row.meralco_rate, row.avg_temperature, row.avg_humidity,
                row.total_rainfall_mm, row.holiday_count, row.weekend_count,
                row.hot_days_count, row.rainy_days_count, row.is_el_nino,
            )

        return results
