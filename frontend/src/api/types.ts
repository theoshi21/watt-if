/**
 * Shared TypeScript types mirroring the FastAPI Pydantic schemas.
 */

export interface ForecastMonth {
  year_month: string;       // YYYY-MM
  kwh_forecast: number;
  kwh_lower_95: number;
  kwh_upper_95: number;
  price_forecast: number;
  price_lower_95: number;
  price_upper_95: number;
}

export interface ForecastMetadata {
  forecast_month: string;
  forecasted_kwh: number;
  forecasted_price: number;
  horizon_label: '1m' | '3m' | '6m';
}

export interface CleaningReport {
  total_rows_received: number;
  rows_with_invalid_year_month: unknown[];
  rows_imputed: unknown[];
  duplicate_rows_removed: number;
  rows_after_cleaning: number;
}

export interface UploadResponse {
  rows_received: number;
  validation_status: 'ok' | 'error';
  cleaning_report: CleaningReport | null;
  retraining_triggered: boolean;
}

export interface ForecastResponse {
  horizon: number;
  months: ForecastMonth[];
}

export interface AskResponse {
  answer: string;
  sources: ForecastMetadata[];
}

export interface ModelInfoResponse {
  trained_at: string | null;
  mape_kwh_pct: number | null;
  mape_price_pct: number | null;
  mape_avg_pct: number | null;
  order: number[] | null;
  seasonal_order: number[] | null;
  training_window_start: string | null;
  training_window_end: string | null;
  rating: 'Excellent' | 'Good' | 'Fair' | 'Poor' | null;
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  subsystems: {
    data_pipeline: 'operational' | 'degraded';
    sarimax_model: 'operational' | 'degraded';
    vector_store: 'operational' | 'degraded';
    llm_service: 'operational' | 'degraded';
  };
}

export type Horizon = 1 | 3 | 6;
