# Requirements Document

## Introduction

WATT-IF is a Progressive Web Application (PWA) for forecasting household electricity consumption and estimated electricity cost. The system ingests historical monthly electricity bill data, enriches it with weather and holiday features aggregated to monthly granularity, trains a SARIMAX time-series model to produce kWh and price forecasts, and surfaces those forecasts through a Retrieval-Augmented Generation (RAG) pipeline powered by Qwen3 8B Instruct. Users interact with the system through a React-based PWA dashboard where they can view forecast charts and ask natural-language questions about their expected electricity usage and costs.

The core pipeline is:
**Monthly electricity bill CSV → data cleaning → weather and holiday feature engineering (monthly) → SARIMAX training → monthly kWh and price forecasting → forecast document storage → vector database → RAG retrieval → Qwen3 8B Instruct → FastAPI backend → React PWA dashboard**

---

## Glossary

- **WATT-IF**: The name of the Progressive Web Application described in this document.
- **SARIMAX_Model**: The Seasonal Autoregressive Integrated Moving Average with Exogenous Variables model responsible for forecasting monthly kWh consumption and electricity price.
- **RAG_System**: The Retrieval-Augmented Generation system that combines ChromaDB vector retrieval with Qwen3 8B Instruct to answer natural-language questions.
- **Forecast_Document**: A structured text representation of SARIMAX model outputs (forecasted kWh and price for a given month) stored in the vector database for retrieval.
- **Data_Pipeline**: The sequence of processing steps that transforms raw monthly electricity bill data into cleaned, feature-engineered training data.
- **Feature_Engineering_Service**: The component responsible for enriching monthly bill records with exogenous variables (monthly mean weather conditions and a public holiday count per month).
- **Vector_Store**: The vector database (ChromaDB) that stores and indexes Forecast_Documents for semantic retrieval.
- **LLM_Service**: The Qwen3 8B Instruct model served locally via Ollama, used to generate natural-language answers from retrieved Forecast_Documents. The API_Server communicates with the LLM_Service over Ollama's local REST API (`http://localhost:11434`).
- **Ollama**: A local LLM runtime that serves the Qwen3 8B Instruct model and exposes a REST API consumed by the API_Server.
- **API_Server**: The FastAPI backend that exposes endpoints for forecast queries and natural-language question answering.
- **PWA_Dashboard**: The React/Vite/TypeScript Progressive Web Application frontend that displays forecast visualizations and the conversational interface.
- **Bill_Dataset**: The raw historical monthly electricity bill records provided by the user, containing at minimum a billing period (year-month), total kWh consumption, and total price fields. Each row represents one complete monthly bill.
- **Exogenous_Variables**: External input variables fed to the SARIMAX_Model — specifically monthly mean temperature, monthly total precipitation, and a public holiday count per month.
- **kWh**: Kilowatt-hours, the unit of electricity consumption.
- **MAPE**: Mean Absolute Percentage Error, the primary evaluation metric for forecast accuracy.
- **MonthlyRecord**: A single cleaned and validated bill record at monthly granularity (`year_month`, `kwh`, `price`).
- **EnrichedRecord**: A `MonthlyRecord` augmented with monthly exogenous variables (`mean_temp_c`, `total_precip_mm`, `holiday_count`).

---

## Requirements

### Requirement 1: Data Ingestion and Cleaning

**User Story:** As a household user, I want to upload my historical monthly electricity bills as a CSV file so that the system can learn from my past consumption patterns.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL accept Bill_Dataset files in CSV format where each row represents one monthly bill, containing at minimum a billing period column (`year_month` in `YYYY-MM` format), a kWh column, and a price column.
2. WHEN a Bill_Dataset file is uploaded and all required columns (`year_month`, `kwh`, `price`) are present, THE Data_Pipeline SHALL return a confirmation message indicating successful validation.
3. IF a Bill_Dataset file is uploaded and any required column (`year_month`, `kwh`, or `price`) is missing, THEN THE Data_Pipeline SHALL return a descriptive error message identifying the missing column(s) and SHALL NOT proceed with further processing.
4. WHEN a Bill_Dataset file is uploaded, THE Data_Pipeline SHALL validate that each `year_month` value conforms to `YYYY-MM` format.
5. IF a Bill_Dataset row contains a `year_month` value that does not conform to `YYYY-MM` format, THEN THE Data_Pipeline SHALL reject the row, record it in the cleaning report with the original unparseable value, and continue processing the remaining rows.
6. IF a Bill_Dataset row contains a null or non-numeric value in the `kwh` or `price` column, THEN THE Data_Pipeline SHALL impute the missing value using linear interpolation between the nearest preceding and following valid values, and flag the row in the cleaning report with the original value and the interpolated replacement.
7. IF a Bill_Dataset row contains a null or non-numeric value in the `kwh` or `price` column and no valid preceding or following value exists for interpolation (i.e., the missing values are consecutive at the start or end of the dataset), THEN THE Data_Pipeline SHALL fill those values using forward-fill if a preceding value exists, or backward-fill if only a following value exists, and flag each affected row in the cleaning report.
8. WHEN duplicate `year_month` entries are detected, THE Data_Pipeline SHALL retain only the last-occurring entry for that month (by row order in the input file), discard all earlier duplicate rows, and log the total count of duplicate rows removed.
9. WHEN cleaning is complete, THE Data_Pipeline SHALL produce a validated list of `MonthlyRecord` objects sorted chronologically by `year_month` and persist them to SQLite for downstream processing.

---

### Requirement 2: Feature Engineering

**User Story:** As a data scientist, I want the system to enrich monthly bill data with weather and holiday context so that the SARIMAX model can capture seasonal and event-driven patterns.

#### Acceptance Criteria

1. WHEN monthly bill data is produced, THE Feature_Engineering_Service SHALL attach the following weather fields for each billing month: monthly mean temperature (°C) and monthly total precipitation (mm), sourced from the open-meteo API.
2. WHEN monthly bill data is produced, THE Feature_Engineering_Service SHALL attach a `holiday_count` integer representing the number of public holidays falling within that calendar month, as defined by the configured national or regional holiday calendar.
3. WHEN monthly bill data is being enriched and weather data for a given month is unavailable from the configured weather source, THE Feature_Engineering_Service SHALL carry forward the most recent available monthly weather values from the immediately preceding month, log a warning identifying the affected month and source month, and continue feature engineering.
4. IF weather data for a given month is unavailable and no prior monthly weather observation exists, THEN THE Feature_Engineering_Service SHALL set weather fields for that month to null, log an error identifying the affected month, and continue feature engineering for the remaining months.
5. IF the configured holiday calendar source is unavailable for a given month, THEN THE Feature_Engineering_Service SHALL default `holiday_count` to 0 for that month, log a warning identifying the affected month, and continue feature engineering.
6. WHEN monthly bill data is produced, THE Feature_Engineering_Service SHALL pass `mean_temp_c`, `total_precip_mm`, and `holiday_count` as numeric exogenous variables to the SARIMAX_Model without any ordinal encoding, as they are already numeric.

---

### Requirement 3: SARIMAX Model Training

**User Story:** As a household user, I want the system to train a forecasting model on my enriched monthly consumption history so that it can produce accurate future estimates.

#### Acceptance Criteria

1. THE SARIMAX_Model SHALL be trained using historical monthly kWh and price as the endogenous target variables, and monthly mean temperature (°C), monthly total precipitation (mm), and monthly holiday count as exogenous variables.
2. WHEN training is initiated, THE SARIMAX_Model SHALL perform automated order selection (p, d, q, P, D, Q, s) using the pmdarima `auto_arima` function configured to minimise AIC, with seasonal period `s=12` reflecting annual seasonality in monthly data.
3. WHEN training is complete, THE SARIMAX_Model SHALL be persisted to disk as a joblib-serialised file containing the fitted model parameters and the selected order values (p, d, q, P, D, Q, s), so that it can be reloaded without retraining.
4. WHEN training is complete, THE SARIMAX_Model SHALL log its MAPE computed on a held-out validation set comprising at least the final 20% of chronologically ordered training records.
5. IF the logged training MAPE exceeds 30%, THEN THE SARIMAX_Model SHALL log a warning indicating that model accuracy is below the acceptable threshold.
6. IF training cannot converge or the input dataset contains fewer than 14 monthly records after cleaning, THEN THE SARIMAX_Model SHALL log an error describing the failure reason and SHALL NOT persist a model artefact to disk.

---

### Requirement 4: Forecast Generation

**User Story:** As a household user, I want the system to generate monthly forecasts for future electricity consumption and costs so that I can plan my budget.

#### Acceptance Criteria

1. WHEN a forecast is requested, THE SARIMAX_Model SHALL produce point forecasts and 95% confidence intervals for kWh consumption and electricity price for each month within the requested forecast horizon; all point forecast values and both bounds of the confidence intervals SHALL be clamped to a minimum of zero.
2. THE SARIMAX_Model SHALL support forecast horizons of 1 month, 3 months, and 6 months.
3. WHEN generating a forecast, THE SARIMAX_Model SHALL require exogenous variable values (`mean_temp_c`, `total_precip_mm`, `holiday_count`) for each month in the forecast horizon.
4. IF exogenous variable values for the forecast horizon are not provided, THEN THE SARIMAX_Model SHALL compute the fallback value for each exogenous variable as the mean of that variable over all available historical monthly records, use those fallback values for the full forecast horizon, and log a warning identifying which variables used fallback values.
5. WHEN a forecast is generated, THE SARIMAX_Model SHALL convert each forecasted month's results into a Forecast_Document and persist it to the Vector_Store.
6. IF the SARIMAX_Model has fewer than 14 monthly historical records available when a forecast is requested, THEN THE SARIMAX_Model SHALL return an error indicating insufficient data and SHALL NOT produce forecast outputs.
7. IF persisting a Forecast_Document to the Vector_Store fails for any forecasted month, THEN THE SARIMAX_Model SHALL retry the persistence operation once; if the retry also fails, THE SARIMAX_Model SHALL log an error identifying the affected forecast month and continue persisting the remaining Forecast_Documents.

---

### Requirement 5: Forecast Document Storage and Retrieval

**User Story:** As a system operator, I want forecast outputs stored in a vector database so that the RAG system can retrieve relevant context for answering user questions.

#### Acceptance Criteria

1. WHEN a Forecast_Document is created, THE Vector_Store SHALL embed it using a sentence-transformers model and index it for semantic similarity search; IF the embedding operation fails, THEN THE Vector_Store SHALL discard the document, raise an error to the caller, and leave the existing index unchanged.
2. WHEN a natural-language query is received, THE Vector_Store SHALL return up to the top-5 most semantically similar Forecast_Documents ranked by cosine similarity; IF fewer than 5 Forecast_Documents exist in the index, THE Vector_Store SHALL return all available documents; IF no Forecast_Documents exist in the index, THE Vector_Store SHALL return an empty result set.
3. THE Vector_Store SHALL store each Forecast_Document with metadata consisting of exactly four fields: `forecast_month` (YYYY-MM string), `forecasted_kwh` (non-negative float), `forecasted_price` (non-negative float), and `horizon_label` (one of `"1m"`, `"3m"`, or `"6m"`).
4. THE Data_Pipeline SHALL NOT store raw Bill_Dataset records in the Vector_Store; only Forecast_Documents derived from SARIMAX_Model outputs SHALL be stored.
5. WHEN a new forecast run is executed, THE Vector_Store SHALL replace any existing Forecast_Document whose `forecast_month` exactly matches a forecast month in the new run, rather than creating a duplicate entry for that month.

---

### Requirement 6: RAG Question Answering

**User Story:** As a household user, I want to ask natural-language questions about my electricity forecast so that I can understand my expected usage and costs without reading raw data.

#### Acceptance Criteria

1. WHEN a user submits a natural-language question, THE RAG_System SHALL retrieve the top-5 relevant Forecast_Documents from the Vector_Store and pass them as context to the LLM_Service.
2. THE LLM_Service SHALL generate a response grounded exclusively in the retrieved Forecast_Documents and SHALL NOT speculate beyond the available forecast data.
3. WHEN zero Forecast_Documents are retrieved from the Vector_Store for a user query, THE LLM_Service SHALL respond with a message stating that no forecast data is currently available to answer the question, and SHALL NOT attempt to generate a forecast-based answer.
4. WHEN one or more Forecast_Documents are retrieved but none contain data for the specific period, metric, or condition referenced in the user's question, THE LLM_Service SHALL respond with a message stating that the requested information is not available in the current forecast.
5. THE RAG_System SHALL support at minimum the following question types: expected consumption for a future month, expected cost for a future month, which month is forecast to have highest consumption, and comparison of forecasted months.
6. WHEN a response is successfully generated, THE LLM_Service SHALL complete generation within 30 seconds of receiving the retrieved Forecast_Documents; IF generation exceeds 30 seconds, THE LLM_Service SHALL terminate the generation and return an error response indicating a timeout.
7. IF the Vector_Store returns an error or is unreachable when the RAG_System attempts retrieval, THEN THE RAG_System SHALL return an error response to the caller indicating that forecast retrieval failed, and SHALL NOT invoke the LLM_Service.
8. THE LLM_Service SHALL NOT be fine-tuned or trained directly on raw Bill_Dataset records; it SHALL operate solely through retrieval of Forecast_Documents.
9. THE API_Server SHALL communicate with the LLM_Service exclusively via Ollama's local REST API at `http://localhost:11434`, using the `qwen3:8b` model tag.
10. IF the Ollama service is unreachable when the RAG_System attempts to invoke the LLM_Service, THEN THE API_Server SHALL return an HTTP 503 response to the caller with a message indicating that the LLM service is unavailable.

---

### Requirement 7: FastAPI Backend

**User Story:** As a developer, I want a RESTful API backend so that the PWA frontend can retrieve forecasts and submit questions through well-defined endpoints.

#### Acceptance Criteria

1. THE API_Server SHALL expose a `POST /forecast` endpoint that accepts a forecast horizon parameter with a value of 1, 3, or 6 (in months) and returns forecasted kWh, price, and 95% confidence intervals for each month in the horizon.
2. THE API_Server SHALL expose a `POST /ask` endpoint that accepts a natural-language question string and returns a natural-language answer generated by the RAG_System.
3. THE API_Server SHALL expose a `POST /upload` endpoint that accepts a Bill_Dataset file in CSV format with a maximum file size of 10 MB, triggers the Data_Pipeline, and returns a synchronous acknowledgement response containing the number of rows received and the validation result.
4. IF a request to any endpoint is malformed or contains invalid parameters, THEN THE API_Server SHALL return an HTTP 422 response with a descriptive error body identifying the invalid field(s) and the reason for rejection.
5. IF an unhandled internal error occurs, THEN THE API_Server SHALL return an HTTP 500 response and log the full stack trace to the server log.
6. THE API_Server SHALL include Cross-Origin Resource Sharing (CORS) headers permitting GET, POST, and OPTIONS requests from the PWA_Dashboard origin.
7. THE API_Server SHALL expose a `GET /health` endpoint that returns HTTP 200 and a status payload listing each subsystem (Data_Pipeline, SARIMAX_Model, Vector_Store, LLM_Service) as "operational" when all subsystems are reachable and functioning.
8. WHEN one or more subsystems are degraded or unreachable, THE `GET /health` endpoint SHALL return HTTP 207 and a status payload listing each subsystem with its individual status (operational or degraded).

---

### Requirement 8: React PWA Dashboard

**User Story:** As a household user, I want an installable web application with forecast visualisations and a chat interface so that I can interact with my electricity data from any device.

#### Acceptance Criteria

1. THE PWA_Dashboard SHALL be installable on desktop and mobile devices via the browser's native install prompt, meeting the PWA installability criteria (service worker, web manifest, HTTPS).
2. THE PWA_Dashboard SHALL display an interactive bar/line chart using Recharts showing forecasted monthly kWh consumption and price over the selected forecast horizon, with the x-axis labelled with month labels (e.g. "Jan 2026") and the y-axis labelled with units (kWh or currency).
3. THE PWA_Dashboard SHALL display 95% confidence interval bands as shaded areas around the forecast line, rendered such that the line is not occluded by the bands.
4. THE PWA_Dashboard SHALL provide a text input field with a maximum of 500 characters and a submit control through which the user can submit natural-language questions to the `POST /ask` endpoint.
5. WHEN a question response is received from the API_Server, THE PWA_Dashboard SHALL display the answer in a conversational message thread with messages ordered chronologically (oldest at top, newest at bottom); IF the display render fails after a successful API response, THEN THE PWA_Dashboard SHALL display an error message informing the user that the answer could not be displayed.
6. WHEN the user selects a forecast horizon of 1 month, 3 months, or 6 months, THE PWA_Dashboard SHALL send a new forecast request to the API_Server and update the forecast chart within 3 seconds of the selection.
7. THE PWA_Dashboard SHALL allow the user to upload a Bill_Dataset CSV file via a file picker control filtered to `.csv` files only, which submits the selected file to the `POST /upload` endpoint.
8. WHEN a file upload is initiated, THE PWA_Dashboard SHALL immediately display a loading indicator and disable the upload control to prevent duplicate submissions.
9. WHEN a file upload completes successfully, THE PWA_Dashboard SHALL dismiss the loading indicator, re-enable the upload control, and display a success notification.
10. WHEN a file upload fails, THE PWA_Dashboard SHALL dismiss the loading indicator, re-enable the upload control, and display an error message describing the failure reason returned by the API_Server.
11. WHEN the PWA_Dashboard is accessed without a network connection, THE PWA_Dashboard SHALL display the most recently cached forecast data (if cached within the last 24 hours) and a persistent banner indicating offline status.

---

### Requirement 9: Model Evaluation and Retraining

**User Story:** As a system operator, I want the model to be evaluated against actuals and retrained periodically so that forecast accuracy is maintained over time.

#### Acceptance Criteria

1. WHEN new Bill_Dataset records are uploaded, IF the new records extend the existing training window by 1 or more complete calendar months, THEN THE SARIMAX_Model SHALL be retrained using the full updated dataset.
2. WHEN retraining is triggered, THE Data_Pipeline SHALL execute the full pipeline from data cleaning through Forecast_Document storage using the updated dataset.
3. IF any step in the retraining pipeline fails, THEN THE Data_Pipeline SHALL log an error identifying the failed step and the failure reason, halt further pipeline execution, and leave the previously trained model artefact and Vector_Store contents unchanged.
4. WHEN retraining is complete, THE API_Server SHALL log both the previous training MAPE and the updated training MAPE, the date of the retraining run, and retain these log entries for a minimum of 90 days.
5. WHEN a retraining run begins, THE SARIMAX_Model SHALL copy the current model artefact to a versioned backup file before overwriting it with the newly trained model, retaining the backup until the next retraining event completes successfully.
6. WHEN the next retraining event completes successfully and a backup model artefact exists, THE SARIMAX_Model SHALL delete the backup artefact from disk.

---

### Requirement 10: Data Privacy and Security

**User Story:** As a household user, I want my electricity bill data to remain private so that sensitive financial information is not exposed.

#### Acceptance Criteria

1. THE API_Server SHALL store Bill_Dataset records in an isolated local database accessible only to the API_Server process, such that no other process or service can read bill records without going through the API_Server.
2. IF THE API_Server receives a file upload request that fails path traversal or injection validation, THEN THE API_Server SHALL reject the request with an HTTP 400 response, return an error message identifying the validation failure, and SHALL NOT write any part of the uploaded content to disk or database.
3. IF a request is made to the API_Server over a non-HTTPS connection in a production deployment, THEN THE API_Server SHALL redirect the request to the HTTPS equivalent URL rather than serving the response over an unencrypted connection.
4. THE Vector_Store SHALL store only Forecast_Documents; it SHALL NOT contain any field whose value is a raw kWh reading, raw price value, or billing month sourced directly from a Bill_Dataset record without aggregation or transformation by the SARIMAX_Model.
5. THE API_Server SHALL ensure that Bill_Dataset records uploaded in one user session are not accessible to requests made outside of that session.
