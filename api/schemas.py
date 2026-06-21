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
        if v not in (1, 3, 6):
            raise ValueError("horizon must be 1, 3, or 6")
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


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: Literal["ok", "degraded"]
    subsystems: dict[str, Literal["operational", "degraded"]]


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
