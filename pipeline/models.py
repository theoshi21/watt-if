"""
Shared Python dataclasses for the WATT-IF pipeline.
Monthly granularity throughout — one record per billing month.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class MonthlyRecord:
    """A single cleaned and validated bill record at monthly granularity."""

    year_month: str          # YYYY-MM
    kwh: float
    price: float
    meralco_rate: float      # PHP/kWh
    avg_temperature: float   # °C
    avg_humidity: float      # %
    total_rainfall_mm: float
    holiday_count: int
    weekend_count: int
    hot_days_count: int
    rainy_days_count: int
    is_el_nino: int          # 0 or 1


@dataclass
class EnrichedRecord:
    """A MonthlyRecord ready for SARIMAX training (all exogenous fields present)."""

    year_month: str
    kwh: float
    price: float
    meralco_rate: float
    avg_temperature: float
    avg_humidity: float
    total_rainfall_mm: float
    holiday_count: int
    weekend_count: int
    hot_days_count: int
    rainy_days_count: int
    is_el_nino: int


@dataclass
class ExogenousRow:
    """Exogenous variable values for a single forecast month."""

    year_month: str
    meralco_rate: float
    avg_temperature: float
    avg_humidity: float
    total_rainfall_mm: float
    holiday_count: int
    weekend_count: int
    hot_days_count: int
    rainy_days_count: int
    is_el_nino: int


@dataclass
class ForecastMonth:
    """Forecast output for a single month including confidence intervals."""

    year_month: str             # YYYY-MM
    kwh_forecast: float         # point forecast, clamped >= 0
    kwh_lower_95: float
    kwh_upper_95: float
    price_forecast: float       # derived: kwh_forecast × meralco_rate
    price_lower_95: float
    price_upper_95: float
    meralco_rate: float         # rate used to derive price
    avg_temperature: float
    avg_humidity: float
    total_rainfall_mm: float
    holiday_count: int
    weekend_count: int
    hot_days_count: int
    rainy_days_count: int
    is_el_nino: int


@dataclass
class ForecastMetadata:
    """Metadata for a forecast document stored in the vector store."""

    forecast_month: str        # YYYY-MM
    forecasted_kwh: float
    forecasted_price: float
    horizon_label: str         # "1m" | "3m" | "6m"
    meralco_rate: float
    avg_temperature: float
    avg_humidity: float
    total_rainfall_mm: float
    holiday_count: int
    weekend_count: int
    hot_days_count: int
    rainy_days_count: int
    is_el_nino: int


@dataclass
class ForecastDocument:
    """Forecast document stored in ChromaDB vector store."""

    id: str                    # "{forecast_month}_{horizon_label}"  e.g. "2026-03_3m"
    text: str                  # human-readable summary for embedding
    metadata: ForecastMetadata


@dataclass
class CleaningReport:
    """Report describing data cleaning operations performed during ingestion."""

    total_rows_received: int
    rows_with_invalid_year_month: list[dict]
    rows_imputed: list[dict]
    duplicate_rows_removed: int
    rows_after_cleaning: int


@dataclass
class IngestResult:
    """Result of a data ingestion operation."""

    validation_status: Literal["ok", "error"]
    error_message: str | None
    row_count: int
    cleaning_report: CleaningReport | None


@dataclass
class TrainingResult:
    """Result returned by SARIMAXModel.train()."""

    order: tuple[int, int, int]
    seasonal_order: tuple[int, int, int, int]
    mape_validation: float
    training_window: dict          # {"start": "YYYY-MM", "end": "YYYY-MM"}
    artefact_path: str


class ModelTrainingError(Exception):
    """Raised when SARIMAX model training fails."""
