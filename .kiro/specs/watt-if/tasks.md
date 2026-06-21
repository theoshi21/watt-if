# Implementation Plan: WATT-IF

## Overview

Implement WATT-IF as a locally-hosted PWA following the pipeline:
Monthly bill CSV upload → Data Pipeline (clean, validate) → Feature Engineering (monthly weather + holiday count) → SARIMAX training (s=12) → Monthly forecast generation → ChromaDB vector store → RAG via Ollama (Qwen3 8B) → FastAPI backend → React/Vite/TypeScript PWA dashboard.

The input CSV has one row per monthly bill (`year_month`, `kwh`, `price`). All forecasting operates at monthly granularity with horizons of 1, 3, and 6 months.

The backend is Python (FastAPI + pmdarima + ChromaDB + SQLite). The frontend is TypeScript/React with Recharts and vite-plugin-pwa.

---

## Tasks

- [x] 1. Update project structure, shared data models, and tooling for monthly granularity
  - Replace `DailyRecord` with `MonthlyRecord` as the primary data unit in `pipeline/models.py`
  - Update `EnrichedRecord` to use `year_month: str` and exogenous fields `mean_temp_c`, `total_precip_mm`, `holiday_count`
  - Replace `ExogenousRow` fields: `year_month: str`, `mean_temp_c: float`, `total_precip_mm: float`, `holiday_count: int`
  - Replace `ForecastDay` with `ForecastMonth` using `year_month: str` instead of `date: date`
  - Update `ForecastDocument` / `ForecastMetadata`: use `forecast_month: str` (YYYY-MM) and `horizon_label` values `"1m"` / `"3m"` / `"6m"`
  - Update `CleaningReport`: replace `rows_with_unparseable_dates` with `rows_with_invalid_year_month`
  - Update `api/schemas.py`: `ForecastRequest.horizon` validated against `{1, 3, 6}`; `ForecastResponse.months: list[ForecastMonth]`; `ForecastMetadata.forecast_month`
  - Update `storage/db.py`: replace `bill_records`, `daily_aggregates`, `monthly_aggregates` with a single `monthly_bill_records` table (`year_month TEXT PRIMARY KEY`, `kwh`, `price`, `session_id`, `created_at`)
  - Update `tests/conftest.py` fixtures to use the new schema
  - _Requirements: 1.1, 3.3, 4.5, 5.3, 7.1, 7.2, 7.3, 9.4, 10.1_

- [x] 2. Rewrite the Data Pipeline (`pipeline/data_pipeline.py`) for monthly input
  - [x] 2.1 Implement column validation, year_month parsing, and row rejection
    - Rewrite `DataPipeline.ingest()`: check for `year_month`, `kwh`, `price` columns (case-insensitive)
    - Return `IngestResult(validation_status="error")` immediately if any required column is absent
    - Validate each `year_month` value against regex `^\d{4}-\d{2}$`; reject non-conforming rows and record them in `CleaningReport.rows_with_invalid_year_month`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 2.2 Write property tests for column validation and year_month validation
    - **Property 1: Column Validation Accepts Complete CSV and Rejects Incomplete CSV**
    - **Validates: Requirements 1.1, 1.2, 1.3**
    - **Property 2: year_month Validation Accepts YYYY-MM and Rejects Non-Conforming Values**
    - **Validates: Requirements 1.4, 1.5**
    - Test file: `tests/pipeline/test_data_pipeline_pbt.py`; use `st.frozensets(COLUMN_NAMES)` and `st.text()`

  - [x] 2.3 Implement kWh/price imputation, deduplication, and persistence
    - Impute null/non-numeric kWh and price using linear interpolation; forward/backward fill at edges; flag each imputed row in `CleaningReport.rows_imputed`
    - Deduplicate by retaining last occurrence per `year_month`; log duplicate count
    - Sort by `year_month` ascending; persist to SQLite `monthly_bill_records` (upsert on `year_month`)
    - Implement `get_monthly_records(start, end)` and `get_training_window_extent()` reading from SQLite
    - _Requirements: 1.6, 1.7, 1.8, 1.9_

  - [ ]* 2.4 Write property tests for imputation, deduplication, and persistence
    - **Property 3: kWh/Price Imputation Produces Correct Interpolated Value**
    - **Validates: Requirements 1.6, 1.7**
    - **Property 4: Deduplication Retains Last Occurrence Per year_month**
    - **Validates: Requirements 1.8**
    - **Property 5: Monthly Records Are Persisted and Retrievable**
    - **Validates: Requirements 1.9**
    - Test file: `tests/pipeline/test_data_pipeline_pbt.py`

- [x] 3. Checkpoint — Data Pipeline
  - Ensure all Data Pipeline tests pass, ask the user if questions arise.

- [x] 4. Implement the Feature Engineering Service (`pipeline/feature_engineering.py`) for monthly data
  - [x] 4.1 Implement monthly weather fetching, carry-forward logic, and holiday count
    - Write `FeatureEngineeringService.enrich()` using the `open-meteo` Python client to attach `mean_temp_c` and `total_precip_mm` for each `MonthlyRecord`
    - Implement carry-forward: if weather is unavailable for a month, use the most recent prior month's observation; log WARNING with affected month and source month
    - If no prior observation exists, set weather fields to null and log ERROR
    - Attach `holiday_count` using the `holidays` library — count of public holidays in the calendar month for the configured country/region; default to 0 and log WARNING if unavailable
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 4.2 Implement `enrich_forecast_horizon()`
    - Implement `enrich_forecast_horizon(months: list[str]) -> list[ExogenousRow]` to return exogenous variable values for a list of future YYYY-MM strings using open-meteo climate forecast data
    - _Requirements: 2.6_

  - [ ]* 4.3 Write property tests for feature engineering enrichment
    - **Property 6: Feature Engineering Produces Complete Enriched Records**
    - **Validates: Requirements 2.1, 2.2, 2.5**
    - Test file: `tests/pipeline/test_feature_engineering_pbt.py`; mock the open-meteo client and `holidays` library

- [x] 5. Implement the SARIMAX Model (`model/sarimax_model.py`) for monthly forecasting
  - [x] 5.1 Implement model training with auto_arima (m=12), MAPE validation, and artefact persistence
    - Write `SARIMAXModel.train()`: 80/10/10 chronological split (80% train, 10% validation for MAPE, 10% test held out); run `pmdarima.auto_arima` with `seasonal=True, m=12`, minimising AIC
    - Compute MAPE on the held-out 10% validation set; log WARNING if MAPE > 30%
    - Persist artefact via `joblib.dump` with fields: `model`, `order`, `seasonal_order` (P, D, Q, 12), `exog_columns`, `trained_at`, `mape_validation`, `training_window`
    - Raise `ModelTrainingError` if dataset has fewer than 14 monthly records or if auto_arima fails to converge
    - Implement `SARIMAXModel.load()` to deserialise from disk
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 5.2 Write property test for training artefact round-trip
    - **Property 7: Training Artefact Round-Trip Preserves All Fields**
    - **Validates: Requirements 3.2, 3.3**
    - Test file: `tests/model/test_sarimax_pbt.py`; use synthetic monthly time series via `st.lists(st.floats(...))`
    - Note: training uses 80/10/10 split (train/validation/test)

  - [x] 5.3 Implement forecast generation with exogenous fallback and value clamping
    - Write `SARIMAXModel.forecast(horizon, exog)`: horizon must be 1, 3, or 6; load persisted model; if `exog` is None, compute fallback means over all available historical months and log a warning
    - Generate point forecasts and 95% CI for kWh and price; clamp all values to `>= 0`
    - Return a list of `ForecastMonth` objects with correct `year_month` labels
    - Reject forecast requests when fewer than 14 historical monthly records are available
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6_

  - [ ]* 5.4 Write property tests for forecast non-negativity and exogenous fallback
    - **Property 8: Forecast Values Are Non-Negative**
    - **Validates: Requirements 4.1**
    - **Property 9: Exogenous Fallback Values Equal Historical Means**
    - **Validates: Requirements 4.4**
    - Test file: `tests/model/test_sarimax_pbt.py`

- [x] 6. Implement the Vector Store (`storage/vector_store.py`) for monthly documents
  - [x] 6.1 Implement Forecast Document embedding, upsert, and query
    - Write `VectorStore.upsert()`: embed document text using `all-MiniLM-L6-v2`; upsert using document ID `"{forecast_month}_{horizon_label}"` (e.g. `"2026-03_3m"`); raise `VectorStoreError` on embedding failure
    - Write `VectorStore.query(question, top_k=5)`: return up to `top_k` documents ranked by cosine similarity; return empty list if collection is empty
    - Write `VectorStore.collection_size()` returning total document count
    - Store each document with metadata: `forecast_month`, `forecasted_kwh`, `forecasted_price`, `horizon_label`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 6.2 Write property tests for vector store persistence, query count, and upsert idempotency
    - **Property 10: Forecast Documents Are Persisted and Retrievable**
    - **Validates: Requirements 4.5, 5.1**
    - **Property 11: Query Results Have Correct Count and Metadata Schema**
    - **Validates: Requirements 5.2, 5.3**
    - **Property 12: Upsert on Duplicate Forecast Month Produces No Duplicates**
    - **Validates: Requirements 5.5**
    - Test file: `tests/storage/test_vector_store_pbt.py`; use in-memory ChromaDB

- [x] 7. Implement the RAG Service (`rag/rag_service.py`)
  - [x] 7.1 Implement retrieval, prompt construction, and Ollama invocation
    - Write `RAGService.answer(question)`: retrieve top-5 `ForecastDocument` objects from `VectorStore`
    - If the vector store is unreachable, return an error response without calling Ollama
    - If zero documents are retrieved, return a "no forecast data is currently available" message
    - Construct the grounded prompt; call `POST http://localhost:11434/api/chat` with model `qwen3:8b`, `stream: false`, `temperature: 0.1`, timeout 30s
    - Return `RAGResponse` with `answer` text and `sources` (list of `ForecastMetadata`)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10_

  - [ ]* 7.2 Write unit tests for RAG service edge cases
    - Test: zero documents → "no forecast data" response, Ollama not called
    - Test: Ollama unreachable → error response, no crash
    - Test: Ollama timeout (mocked) → timeout error response
    - Test file: `tests/rag/test_rag_service.py`

- [x] 8. Checkpoint — ML Pipeline and RAG
  - Ensure all pipeline, model, vector store, and RAG tests pass, ask the user if questions arise.

- [x] 9. Implement the FastAPI API Server (`api/main.py`)
  - [x] 9.1 Implement `POST /upload` with validation and pipeline trigger
    - Accept `multipart/form-data`; enforce file size ≤ 10 MB; accept `.csv` only
    - Perform path traversal / injection validation; return HTTP 400 on failure
    - On success, invoke `DataPipeline.ingest()`; return `UploadResponse`
    - _Requirements: 7.3, 7.4, 10.2_

  - [x] 9.2 Implement `POST /forecast` and `POST /ask`
    - Wire `POST /forecast` with `ForecastRequest {horizon: int, must be 1, 3, or 6}`; load SARIMAX model, run `forecast()`, upsert each `ForecastMonth` as a `ForecastDocument`, return `ForecastResponse`
    - Wire `POST /ask` with `AskRequest {question: str [1-500 chars]}`; invoke `RAGService.answer()`; return `AskResponse`; return HTTP 503 if Ollama unreachable
    - _Requirements: 7.1, 7.2, 6.9, 6.10_

  - [x] 9.3 Implement `GET /health`, CORS middleware, and error handlers
    - Wire `GET /health`: probe each subsystem; return HTTP 200 / 207 as appropriate
    - Add `CORSMiddleware` for `http://localhost:5173`
    - Register global exception handler returning HTTP 500 with stack trace logged
    - _Requirements: 7.4, 7.5, 7.6, 7.7, 7.8_

  - [ ]* 9.4 Write property tests for API endpoint correctness and invalid input handling
    - **Property 13: Forecast Endpoint Returns Correct Month Count for Any Valid Horizon**
    - **Validates: Requirements 7.1**
    - **Property 14: Invalid API Inputs Return HTTP 422 with Field-Level Errors**
    - **Validates: Requirements 7.4**
    - **Property 15: Health Endpoint Reflects Subsystem State**
    - **Validates: Requirements 7.7, 7.8**
    - **Property 21: Path Traversal Filenames Are Rejected with HTTP 400**
    - **Validates: Requirements 10.2**
    - **Property 22: Session Isolation Prevents Cross-Session Data Access**
    - **Validates: Requirements 10.5**
    - Test file: `tests/api/test_api_pbt.py`; use FastAPI `TestClient`

- [x] 10. Implement model retraining pipeline (`model/retraining.py`)
  - [x] 10.1 Implement retraining trigger check and pipeline orchestration
    - Write `RetrainingService` reading training window via `DataPipeline.get_training_window_extent()`
    - After each successful upload, compare `new_latest_year_month` vs `previous_latest_year_month`; trigger retraining if `new > previous`
    - Orchestrate: data cleaning → feature engineering → SARIMAX training → forecast generation → vector store update
    - On failure at any step, log ERROR, halt, leave existing artefact and vector store unchanged
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 10.2 Implement model backup and post-retraining log
    - Before overwriting the model artefact, call `SARIMAXModel.backup()`
    - On successful completion, call `SARIMAXModel.delete_backup()`
    - Write a `training_log` record to SQLite; retain entries for ≥ 90 days
    - _Requirements: 9.4, 9.5, 9.6_

  - [ ]* 10.3 Write property tests for retraining trigger condition and failure semantics
    - **Property 18: Retraining Is Triggered If and Only If a New Calendar Month Is Added**
    - **Validates: Requirements 9.1**
    - **Property 19: Failed Retraining Leaves Existing Model Artefact Unchanged**
    - **Validates: Requirements 9.3**
    - **Property 20: Model Backup Is Created Before Artefact Is Overwritten**
    - **Validates: Requirements 9.5, 9.6**
    - Test file: `tests/model/test_retraining_pbt.py`

- [x] 11. Checkpoint — Backend API and Retraining
  - Ensure all API and retraining tests pass, ask the user if questions arise.

- [x] 12. Implement the React PWA frontend (`frontend/src/`)
  - [x] 12.1 Scaffold Vite/TypeScript project with PWA configuration and API client
    - Initialise Vite project with React + TypeScript template inside `frontend/`
    - Configure `vite-plugin-pwa`: `CacheFirst` for static assets, `NetworkFirst` 24h TTL for `/forecast`, `NetworkOnly` for `/ask`
    - Create `public/manifest.json` meeting PWA installability criteria
    - Write typed API client `src/api/client.ts` for `POST /upload`, `POST /forecast`, `POST /ask`, `GET /health`
    - _Requirements: 8.1, 8.11_

  - [x] 12.2 Implement `ForecastChart` and `HorizonSelector` components
    - Build `ForecastChart` as a Recharts `ComposedChart` with `Bar` (monthly kWh/price), `Area` (95% CI bands); x-axis labelled with month strings (e.g. "Jan 2026"), y-axis with units
    - Build `HorizonSelector` as a button group for 1m / 3m / 6m; triggers `POST /forecast`; chart updates within 3 seconds
    - _Requirements: 8.2, 8.3, 8.6_

  - [ ]* 12.3 Write property test for ForecastChart CI band rendering
    - **Property 16: Forecast Chart Renders CI Bands for All Forecast Data**
    - **Validates: Requirements 8.3**
    - Test file: `tests/frontend/test_forecast_chart.test.tsx`; use fast-check with `ForecastMonth` records

  - [x] 12.4 Implement `ChatPanel` component
    - Scrollable message thread (oldest top, newest bottom), 500-char max input, submit button
    - On submit, call `POST /ask`; append question/answer pair; show error in thread if render fails
    - _Requirements: 8.4, 8.5_

  - [ ]* 12.5 Write property test for chat thread chronological ordering
    - **Property 17: Chat Thread Maintains Chronological Message Order**
    - **Validates: Requirements 8.5**
    - Test file: `tests/frontend/test_chat_panel.test.tsx`

  - [x] 12.6 Implement `UploadPanel`, `OfflineBanner`, and `HealthIndicator` components
    - `UploadPanel`: `.csv`-filtered file picker; spinner + disable on upload start; success/error notification on completion
    - `OfflineBanner`: checks `navigator.onLine`, subscribes to `online`/`offline` events; shows persistent banner + cached forecast when offline
    - `HealthIndicator`: polls `GET /health` on mount, displays per-subsystem status
    - _Requirements: 8.7, 8.8, 8.9, 8.10, 8.11_

- [x] 13. Wire all components into the App and run integration smoke checks
  - [x] 13.1 Wire all frontend components into the root `App` component
    - Compose all components in `App.tsx`; ensure state flows correctly
    - _Requirements: 8.1, 8.2, 8.4, 8.7_

  - [ ]* 13.2 Write integration tests for the full backend pipeline
    - Full Data Pipeline run: monthly CSV → SQLite (real `:memory:`, mocked open-meteo)
    - Full Forecast run: load model → forecast months → persist to ChromaDB → query
    - Full RAG run: question → ChromaDB retrieval → mocked Ollama → `AskResponse`
    - Retraining pipeline: upload new month → threshold check → retrain → new artefact
    - Test file: `tests/integration/test_pipeline_integration.py`

- [x] 14. Final checkpoint — Ensure all tests pass
  - Ensure all backend and frontend tests pass, ask the user if questions arise.

---

## Notes

- The input CSV has exactly one row per billing month: `year_month` (YYYY-MM), `kwh`, `price`
- SARIMAX is trained with `s=12` (annual seasonality) on monthly data
- Forecast horizons are strictly 1, 3, or 6 months — not a continuous range
- `horizon_label` values in vector store metadata are `"1m"`, `"3m"`, `"6m"`
- Tasks marked `*` are optional PBT tasks — skip for a faster MVP
- The Hypothesis library (`@given`, `settings(max_examples=100)`) is used for backend PBTs; fast-check for React component PBTs
- Ollama must be running locally on `localhost:11434` with `qwen3:8b` pulled before the RAG service can function
- The SQLite `monthly_bill_records` table uses `session_id` to enforce session isolation per Requirement 10.5
- The retraining trigger condition is: `new_latest_year_month > previous_latest_year_month` (at least one new complete month added)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "6.1"] },
    { "id": 2, "tasks": ["2.2", "2.3"] },
    { "id": 3, "tasks": ["2.4", "4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3"] },
    { "id": 5, "tasks": ["5.1"] },
    { "id": 6, "tasks": ["5.2", "5.3", "6.2"] },
    { "id": 7, "tasks": ["5.4", "7.1"] },
    { "id": 8, "tasks": ["7.2", "9.1"] },
    { "id": 9, "tasks": ["9.2", "9.3", "10.1"] },
    { "id": 10, "tasks": ["9.4", "10.2"] },
    { "id": 11, "tasks": ["10.3", "12.1"] },
    { "id": 12, "tasks": ["12.2"] },
    { "id": 13, "tasks": ["12.3", "12.4"] },
    { "id": 14, "tasks": ["12.5", "12.6"] },
    { "id": 15, "tasks": ["13.1"] },
    { "id": 16, "tasks": ["13.2"] }
  ]
}
```
