"""
Pydantic API request/response models for the WATT-IF FastAPI server.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from pipeline.models import CleaningReport, ExogenousRow, ForecastMonth, ForecastMetadata


class ForecastRequest(BaseModel):
    """Request body for POST /forecast."""

    horizon: int = Field(..., description="Forecast horizon in months: must be 1, 3, or 6.")
    exog: list[ExogenousRow] | None = Field(
        default=None,
        description=(
            "Optional exogenous variable values for each month in the horizon. "
            "If omitted, fallback means over all available historical months are used."
        ),
    )

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("horizon")
    @classmethod
    def horizon_must_be_valid(cls, v: int) -> int:
        if v not in (1, 3, 6, 9, 12):
            raise ValueError("horizon must be 1, 3, 6, 9, or 12")
        return v


class ForecastResponse(BaseModel):
    """Response body for POST /forecast."""

    horizon: int
    months: list[ForecastMonth]

    model_config = {"arbitrary_types_allowed": True}


class AskRequest(BaseModel):
    """Request body for POST /ask."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural-language question about electricity forecasts (1–500 chars).",
    )


class AskResponse(BaseModel):
    """Response body for POST /ask."""

    answer: str
    sources: list[ForecastMetadata]

    model_config = {"arbitrary_types_allowed": True}


class UploadResponse(BaseModel):
    """Response body for POST /upload."""

    rows_received: int
    validation_status: str
    cleaning_report: CleaningReport | None
    retraining_triggered: bool

    model_config = {"arbitrary_types_allowed": True}


class DataEntryCreate(BaseModel):
    """Request body for POST /data-entries."""

    year_month: str = Field(..., description="YYYY-MM")
    kwh: float = Field(..., gt=0, le=1_000_000)
    bill_amount: float | None = Field(default=None, ge=0)
    rate_override: float | None = Field(default=None, gt=0, description="Override the auto-resolved Meralco rate (₱/kWh)")
    label: str | None = Field(default=None, max_length=100)
    source: Literal["Manual", "CSV Upload"]

    @field_validator("year_month")
    @classmethod
    def validate_year_month(cls, v: str) -> str:
        import re
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", v):
            raise ValueError("year_month must be YYYY-MM with month 01–12")
        return v


class DataEntryRow(BaseModel):
    """Response body for GET /data-entries and POST /data-entries.

    Includes the resolved exogenous variable values from monthly_bill_records
    so the UI can display exactly what the model will train on.
    """

    id: int
    year_month: str
    kwh: float
    bill_amount: float | None
    label: str | None
    source: str
    created_at: str
    # Resolved exog fields from monthly_bill_records (None when not yet bridged)
    meralco_rate: float | None = None
    avg_temperature: float | None = None
    avg_humidity: float | None = None
    total_rainfall_mm: float | None = None
    holiday_count: int | None = None
    weekend_count: int | None = None
    hot_days_count: int | None = None
    rainy_days_count: int | None = None
    is_el_nino: int | None = None
    enso_phase: int | None = None   # -1 La Niña | 0 Neutral | 1 El Niño


class DataEntryUpdate(BaseModel):
    """Request body for PUT /data-entries/{id} — all fields optional."""

    kwh: float | None = Field(default=None, gt=0, le=1_000_000)
    bill_amount: float | None = Field(default=None, ge=0)
    label: str | None = Field(default=None, max_length=100)


class ChatMessageCreate(BaseModel):
    """Request body for POST /chat-history."""

    role: Literal["user", "assistant"]
    text: str = Field(..., min_length=1, max_length=10_000)


class ChatMessageRow(BaseModel):
    """Response body for GET /chat-history and POST /chat-history."""

    id: int
    role: str
    text: str
    created_at: str


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: Literal["ok", "degraded"]
    subsystems: dict[str, Literal["operational", "degraded"]]


class RateBracketResponse(BaseModel):
    """One consumption bracket within a customer type."""
    bracket_key: str
    bracket_label: str
    generation_charge_per_kwh: float
    transmission_charge_per_kwh: float
    system_loss_per_kwh: float
    distribution_charge_per_kwh: float
    supply_per_kwh: float
    supply_fixed_monthly: float
    metering_per_kwh: float
    metering_fixed_monthly: float
    other_charges_per_kwh: float
    residential_rate_per_kwh: float


class CustomerTypeResponse(BaseModel):
    """One customer type with its brackets."""
    type_key: str
    type_label: str
    brackets: list[RateBracketResponse]


class MeralcoRateResponse(BaseModel):
    """Response body for GET /meralco-rate and POST /meralco-rate/refresh."""
    customer_types: list[CustomerTypeResponse]
    fetched_at: str
    is_fallback: bool
    effective_month: str


class ModelInfoResponse(BaseModel):
    """Response body for GET /model-info."""

    trained_at: str | None
    mape_kwh_pct: float | None        # validation MAPE for kWh, as a percentage
    mape_price_pct: float | None      # validation MAPE for price, as a percentage
    mape_avg_pct: float | None        # average of the two, as a percentage
    order: list[int] | None           # ARIMA (p, d, q)
    seasonal_order: list[int] | None  # Seasonal (P, D, Q, m)
    training_window_start: str | None
    training_window_end: str | None
    rating: str | None                # "Excellent" / "Good" / "Fair" / "Poor"


class SavedForecastResponse(BaseModel):
    """Response body for GET /saved-forecast."""

    horizon: int | None = None
    months: list[dict] | None = None
    saved_at: str | None = None


class SaveForecastRequest(BaseModel):
    """Request body for POST /saved-forecast — accepts partial month data from the frontend."""

    horizon: int
    months: list[dict]
