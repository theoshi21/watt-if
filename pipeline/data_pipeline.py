"""
Data Pipeline for WATT-IF.

Responsible for ingesting, cleaning, and persisting raw monthly CSV bill data.

Covers tasks 2.1 and 2.3:
  - Column presence validation (year_month, kwh, price required; new columns optional with defaults)
  - year_month format validation via regex (Req 1.4, 1.5)
  - Numeric imputation for all numeric columns (linear interpolation, ffill/bfill) (Req 1.6, 1.7)
  - Deduplication — keep last occurrence per year_month (Req 1.8)
  - Persist to SQLite monthly_bill_records (upsert on year_month) (Req 1.9)
  - Query helpers: get_monthly_records, get_training_window_extent
"""

from __future__ import annotations

import logging
import re
import sqlite3
from datetime import datetime, timezone

import pandas as pd

from pipeline.models import (
    CleaningReport,
    IngestResult,
    MonthlyRecord,
)

logger = logging.getLogger(__name__)

# Columns that MUST be present in the uploaded CSV.
REQUIRED_COLUMNS = {"year_month", "kwh", "price"}

# New exogenous columns — optional in upload but filled with defaults when absent.
EXOG_COLUMNS_WITH_DEFAULTS: dict[str, float] = {
    "meralco_rate": 0.0,
    "avg_temperature": 0.0,
    "avg_humidity": 0.0,
    "total_rainfall_mm": 0.0,
    "holiday_count": 0.0,
    "weekend_count": 0.0,
    "hot_days_count": 0.0,
    "rainy_days_count": 0.0,
    "is_el_nino": 0.0,
}

# All numeric columns to impute.
_NUMERIC_COLUMNS = ["kwh", "price"] + list(EXOG_COLUMNS_WITH_DEFAULTS.keys())

_YEAR_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


class DataPipeline:
    """Pipeline for ingesting, cleaning, and persisting monthly electricity bill data."""

    def __init__(self, db_conn: sqlite3.Connection) -> None:
        self._conn = db_conn

    def ingest(self, file_path: str, session_id: str = "default", user_id: int | None = None) -> IngestResult:
        """Validate, clean, and ingest a monthly CSV bill dataset."""

        # Step 0 — Load CSV
        try:
            df = pd.read_csv(file_path)
        except Exception as exc:
            logger.error("Failed to read CSV file %s: %s", file_path, exc)
            return IngestResult(
                validation_status="error",
                error_message=f"Failed to read file: {exc}",
                row_count=0,
                cleaning_report=None,
            )

        total_rows = len(df)
        df.columns = [c.strip().lower() for c in df.columns]

        # Step 1 — Required column check
        missing_columns = sorted(REQUIRED_COLUMNS - set(df.columns))
        if missing_columns:
            error_msg = f"Missing required column(s): {', '.join(missing_columns)}"
            logger.error(error_msg)
            return IngestResult(
                validation_status="error",
                error_message=error_msg,
                row_count=0,
                cleaning_report=None,
            )

        # Step 1b — Add missing optional exogenous columns with defaults
        for col, default in EXOG_COLUMNS_WITH_DEFAULTS.items():
            if col not in df.columns:
                logger.info("Optional column '%s' not in CSV; defaulting to %s.", col, default)
                df[col] = default

        # Step 2 — year_month format validation
        rows_with_invalid_year_month: list[dict] = []
        df["year_month"] = df["year_month"].astype(str).str.strip()
        invalid_mask = ~df["year_month"].str.match(r"^\d{4}-\d{2}$", na=False)
        if invalid_mask.any():
            for idx in df.index[invalid_mask]:
                rows_with_invalid_year_month.append(
                    {"row_index": int(idx), "original_value": df.at[idx, "year_month"]}
                )
        df = df.loc[~invalid_mask].copy()

        # Step 3 — Numeric imputation for all numeric columns
        rows_imputed: list[dict] = []
        for col in _NUMERIC_COLUMNS:
            raw_col = df[col].copy()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            null_mask = df[col].isna()
            if null_mask.any():
                df[col] = df[col].interpolate(method="linear").ffill().bfill()
                for idx in df.index[null_mask]:
                    rows_imputed.append({
                        "row_index": int(idx),
                        "field": col,
                        "original": raw_col.at[idx],
                        "replacement": df.at[idx, col],
                    })

        # Step 4 — Deduplication (keep last)
        rows_before_dedup = len(df)
        df = df[~df.duplicated(subset=["year_month"], keep="last")].copy()
        duplicate_rows_removed = rows_before_dedup - len(df)

        # Step 5 — Sort
        df = df.sort_values("year_month").reset_index(drop=True)

        # Step 6 — Persist to SQLite (with user_id for composite PK isolation)
        created_at = datetime.now(timezone.utc).isoformat()
        cursor = self._conn.cursor()
        cursor.executemany(
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
            [
                (
                    row["year_month"],
                    float(row["kwh"]),
                    float(row["price"]),
                    float(row["meralco_rate"]),
                    float(row["avg_temperature"]),
                    float(row["avg_humidity"]),
                    float(row["total_rainfall_mm"]),
                    int(row["holiday_count"]),
                    int(row["weekend_count"]),
                    int(row["hot_days_count"]),
                    int(row["rainy_days_count"]),
                    int(row["is_el_nino"]),
                    session_id,
                    created_at,
                    user_id,
                )
                for _, row in df.iterrows()
            ],
        )
        self._conn.commit()

        cleaning_report = CleaningReport(
            total_rows_received=total_rows,
            rows_with_invalid_year_month=rows_with_invalid_year_month,
            rows_imputed=rows_imputed,
            duplicate_rows_removed=duplicate_rows_removed,
            rows_after_cleaning=len(df),
        )

        return IngestResult(
            validation_status="ok",
            error_message=None,
            row_count=len(df),
            cleaning_report=cleaning_report,
        )

    def get_monthly_records(self, start: str, end: str, user_id: int | None = None) -> list[MonthlyRecord]:
        """Return monthly bill records from SQLite between start and end (inclusive)."""
        cursor = self._conn.cursor()
        if user_id is not None:
            cursor.execute(
                """
                SELECT year_month, kwh, price, meralco_rate, avg_temperature, avg_humidity,
                       total_rainfall_mm, holiday_count, weekend_count, hot_days_count,
                       rainy_days_count, is_el_nino
                FROM monthly_bill_records
                WHERE year_month BETWEEN ? AND ? AND user_id = ?
                ORDER BY year_month
                """,
                (start, end, user_id),
            )
        else:
            cursor.execute(
                """
                SELECT year_month, kwh, price, meralco_rate, avg_temperature, avg_humidity,
                       total_rainfall_mm, holiday_count, weekend_count, hot_days_count,
                       rainy_days_count, is_el_nino
                FROM monthly_bill_records
                WHERE year_month BETWEEN ? AND ?
                ORDER BY year_month
                """,
                (start, end),
            )
        rows = cursor.fetchall()
        return [
            MonthlyRecord(
                year_month=row["year_month"],
                kwh=row["kwh"],
                price=row["price"],
                meralco_rate=row["meralco_rate"],
                avg_temperature=row["avg_temperature"],
                avg_humidity=row["avg_humidity"],
                total_rainfall_mm=row["total_rainfall_mm"],
                holiday_count=row["holiday_count"],
                weekend_count=row["weekend_count"],
                hot_days_count=row["hot_days_count"],
                rainy_days_count=row["rainy_days_count"],
                is_el_nino=row["is_el_nino"],
            )
            for row in rows
        ]

    def get_training_window_extent(self, user_id: int | None = None) -> tuple[str, str]:
        """Return (earliest_year_month, latest_year_month) of persisted records."""
        cursor = self._conn.cursor()
        if user_id is not None:
            cursor.execute(
                "SELECT MIN(year_month), MAX(year_month) FROM monthly_bill_records WHERE user_id = ?",
                (user_id,),
            )
        else:
            cursor.execute(
                "SELECT MIN(year_month), MAX(year_month) FROM monthly_bill_records"
            )
        row = cursor.fetchone()
        min_ym, max_ym = row[0], row[1]
        if min_ym is None or max_ym is None:
            raise ValueError(
                "No records found in monthly_bill_records; "
                "cannot determine training window extent."
            )
        return min_ym, max_ym
