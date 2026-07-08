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
  avg_temperature: number;
  avg_humidity: number;
}

export interface ForecastMetadata {
  forecast_month: string;
  forecasted_kwh: number;
  forecasted_price: number;
  horizon_label: '1m' | '3m' | '6m' | '9m' | '12m';
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
  warnings?: string[];
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

export interface DataEntryCreate {
  year_month: string;
  kwh: number;
  bill_amount?: number | null;
  rate_override?: number | null;
  label?: string | null;
  source: 'Manual' | 'CSV Upload';
}

export interface DataEntryRow {
  id: number;
  year_month: string;
  kwh: number;
  bill_amount: number | null;
  label: string | null;
  source: string;
  created_at: string;
  // Exog fields from monthly_bill_records (null if not bridged)
  meralco_rate: number | null;
  avg_temperature: number | null;
  avg_humidity: number | null;
  total_rainfall_mm: number | null;
  holiday_count: number | null;
  weekend_count: number | null;
  hot_days_count: number | null;
  rainy_days_count: number | null;
  is_el_nino: number | null;
  enso_phase: number | null; // -1 La Niña | 0 Neutral | 1 El Niño
}

export interface DataEntryUpdate {
  kwh?: number | null;
  bill_amount?: number | null;
  label?: string | null;
}

export interface ChatMessageCreate {
  role: 'user' | 'assistant';
  text: string;
}

export interface ChatMessageRow {
  id: number;
  role: string;
  text: string;
  created_at: string;
}

export type Horizon = 1 | 3 | 6 | 9 | 12;

export interface RateBracket {
  bracket_key: string;
  bracket_label: string;
  generation_charge_per_kwh: number;
  transmission_charge_per_kwh: number;
  system_loss_per_kwh: number;
  distribution_charge_per_kwh: number;
  supply_per_kwh: number;
  supply_fixed_monthly: number;
  metering_per_kwh: number;
  metering_fixed_monthly: number;
  other_charges_per_kwh: number;
  residential_rate_per_kwh: number;
}

export interface CustomerType {
  type_key: string;
  type_label: string;
  brackets: RateBracket[];
}

export interface MeralcoRateResponse {
  customer_types: CustomerType[];
  fetched_at: string;
  is_fallback: boolean;
  effective_month: string;
}

export interface UserSettings {
  customer_type: 'Residential' | 'General Service A' | 'General Service B';
  default_forecast_horizon: Horizon;
  rate_override: number | null;
  chat_max_history: number;
  chat_auto_clear: boolean;
  notify_kwh_budget: number | null;
  notify_bill_ceiling: number | null;
  notify_high_consumption: number | null;
  auto_retrain_on_upload: boolean;
  min_datapoints_to_train: number;
}

export interface UserSettingsUpdate {
  customer_type?: string;
  default_forecast_horizon?: number;
  rate_override?: number | null;
  chat_max_history?: number;
  chat_auto_clear?: boolean;
  notify_kwh_budget?: number | null;
  notify_bill_ceiling?: number | null;
  notify_high_consumption?: number | null;
  auto_retrain_on_upload?: boolean;
  min_datapoints_to_train?: number;
}
