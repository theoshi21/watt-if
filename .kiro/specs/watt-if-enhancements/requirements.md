# Requirements Document

## Introduction

This document specifies requirements for five enhancement areas of the WATT-IF energy intelligence web application. The enhancements cover sidebar branding, expanded forecast horizon options, live weather data on the dashboard, and two persistent server-side storage features (data entry log and chat history) backed by the existing SQLite database.

## Glossary

- **Sidebar**: The persistent left-hand navigation panel rendered by `Sidebar.tsx`.
- **Horizon**: The number of months ahead for which the SARIMAX model generates a forecast. Currently `1 | 3 | 6`; to be extended to `1 | 3 | 6 | 9 | 12`.
- **HorizonSelector**: The React component (`HorizonSelector.tsx`) that renders horizon toggle buttons.
- **ForecastContext**: The React context (`ForecastContext.tsx`) that holds the active horizon and forecast data.
- **ForecastMonth**: A single month of forecast output, containing kWh, price, confidence intervals, and exogenous variables including `avg_temperature` and `avg_humidity`.
- **Dashboard**: The main landing page rendered by `DashboardPage.tsx`, showing stat cards and a consumption chart.
- **StatCard**: A small UI card component (`StatCard.tsx`) that displays a labelled numeric value with a unit.
- **DataEntryLog**: The server-side SQLite table and associated REST API that persists manual bill entries and CSV upload events.
- **DataEntry_Page**: The React page (`DataEntryPage.tsx`) that provides the manual entry form, upload panel, and entry history table.
- **ChatHistory**: The server-side SQLite table and associated REST API that persists chat message pairs across browser sessions.
- **ChatPanel**: The React component (`ChatPanel.tsx`) that renders the conversational Q&A interface.
- **DB**: The SQLite database stored at `data/wattif.db`, managed via `storage/db.py`.
- **API**: The FastAPI backend server in `api/main.py`, reachable at `http://localhost:8000`.
- **Client**: The typed API client in `frontend/src/api/client.ts` used by all frontend components.
- **ForecastRequest**: The Pydantic request model in `api/schemas.py` for `POST /forecast`.
- **HORIZON_LABELS**: The dict `_HORIZON_LABELS` in `api/main.py` mapping horizon integers to label strings.

---

## Requirements

### Requirement 1: Sidebar Branding

**User Story:** As a user, I want to see the WATT-IF product name displayed prominently in the sidebar, so that the application identity is clear at a glance.

#### Acceptance Criteria

1. THE Sidebar SHALL display the logo image, a "WATT-IF" name label, and an "ENERGY INTELLIGENCE" subtitle, stacked vertically in that order within the logo section.
2. WHEN the Sidebar renders, THE Sidebar SHALL display the "WATT-IF" label using `--font-sans`, `font-weight: 700`, `font-size: 1rem`, and `color: var(--color-text-secondary)`, making it visually larger and more prominent than the subtitle below it.
3. WHEN the Sidebar renders, THE Sidebar SHALL display the "ENERGY INTELLIGENCE" subtitle using `--font-mono`, `text-transform: uppercase`, `letter-spacing: 0.12em`, `font-size: 0.65rem`, and `color: var(--color-text-muted)`, preserving the existing monospaced style.
4. THE Sidebar SHALL preserve all existing navigation links, health indicator, model status pill, and settings link, allowing only necessary updates for bug fixes or accessibility improvements while preserving their core functionality and placement.

---

### Requirement 2: Extended Forecast Horizons

**User Story:** As a user, I want to generate forecasts for 9 and 12 months ahead, so that I can plan electricity budgets further into the future.

#### Acceptance Criteria

1. THE HorizonSelector SHALL render exactly five buttons for horizons 1, 3, 6, 9, and 12 months, labelled "1m", "3m", "6m", "9m", and "12m" respectively, in that order.
2. WHEN a user clicks a horizon button (including the currently selected one), THE HorizonSelector SHALL invoke the `onChange` callback with the clicked horizon value.
3. THE ForecastContext SHALL accept and store a selected horizon value from the set `{1, 3, 6, 9, 12}`, with a default value of 3.
4. WHEN a forecast is requested with horizon 9 or 12, THE ForecastRequest validator SHALL accept the value and not raise a validation error.
5. IF a forecast is requested with a horizon value not in `{1, 3, 6, 9, 12}`, THEN THE ForecastRequest validator SHALL return an HTTP 422 error with a message identifying the invalid value.
6. THE HORIZON_LABELS dict SHALL contain entries for all five valid keys: `{1: "1m", 3: "3m", 6: "6m", 9: "9m", 12: "12m"}`.
7. THE `Horizon` type in `frontend/src/api/types.ts` SHALL be the union `1 | 3 | 6 | 9 | 12`.
8. THE `ForecastMetadata` `horizon_label` field in `frontend/src/api/types.ts` SHALL be the union `'1m' | '3m' | '6m' | '9m' | '12m'`.

---

### Requirement 3: Dashboard Temperature and Humidity from Forecast Data

**User Story:** As a user, I want the dashboard to show the forecasted average temperature and humidity for the current month, so that I can understand the environmental factors behind my consumption prediction.

#### Acceptance Criteria

1. THE `ForecastMonth` interface in `frontend/src/api/types.ts` SHALL include `avg_temperature` (number, degrees Celsius) and `avg_humidity` (number, percentage) fields.
2. WHEN `months[0].avg_temperature` is a finite number, THE Dashboard SHALL display it rounded to one decimal place in a StatCard labelled "Avg Temp" with unit "°C".
3. WHEN `months[0].avg_humidity` is a finite number, THE Dashboard SHALL display it rounded to one decimal place in a StatCard labelled "Avg Humidity" with unit "%".
4. WHEN the `months` array is empty or either field is null, undefined, or non-finite, THE Dashboard SHALL display "—" in the corresponding StatCard without crashing.
5. THE Dashboard SHALL always render all four StatCards (This Month, Daily Average, Avg Temp, Avg Humidity) in the stat grid, replacing the previously labelled "Temp Today" and "Humidity" cards.

---

### Requirement 4: Persistent Data Entry History

**User Story:** As a user, I want my monthly bill entries and CSV uploads to persist across page refreshes and devices, so that I have a reliable history of all data I have contributed to the system.

#### Acceptance Criteria

1. THE DB SHALL contain a `data_entry_log` table with columns: `id` (integer primary key autoincrement), `year_month` (text, YYYY-MM, not null), `kwh` (real, not null), `bill_amount` (real, nullable), `label` (text, nullable), `source` (text, not null, one of "Manual" or "CSV Upload"), `created_at` (text ISO 8601, not null).
2. THE API SHALL expose a `GET /data-entries` endpoint that returns all rows from `data_entry_log` ordered by `created_at` descending.
3. THE API SHALL expose a `POST /data-entries` endpoint that accepts a JSON body with fields `year_month` (required), `kwh` (required), `bill_amount` (optional), `label` (optional), `source` (required, "Manual" or "CSV Upload") and persists a new row to `data_entry_log`.
4. IF `year_month` is missing or not in the format `YYYY-MM` (4-digit year, hyphen, 2-digit month 01–12), THEN THE `POST /data-entries` endpoint SHALL return HTTP 422 identifying the `year_month` constraint violated.
5. IF `kwh` is missing, zero, negative, or greater than 1,000,000, THEN THE `POST /data-entries` endpoint SHALL return HTTP 422 identifying the `kwh` constraint violated.
6. IF `source` is missing or not one of "Manual" or "CSV Upload", THEN THE `POST /data-entries` endpoint SHALL return HTTP 422 identifying the `source` constraint violated.
7. THE DataEntry_Page form SHALL contain exactly four fields: a Month picker (`input type="month"`, required, producing YYYY-MM), a kWh number input (required, min 0 exclusive, max 1,000,000), an optional Bill Amount number input in PHP (min 0), and an optional Label text input (maxLength 100).
8. WHEN a user submits the manual entry form with a valid `year_month` and `kwh`, THE DataEntry_Page SHALL call `POST /data-entries` and, upon success, refresh the displayed history table without a full page reload and reset the form to its empty default state.
9. WHEN a CSV upload completes successfully and the server reports at least one row was parsed and validated, THE DataEntry_Page SHALL call `POST /data-entries` with `source` set to "CSV Upload" and the filename as the `label`. THE DataEntry_Page SHALL NOT log a CSV Upload event when no file was successfully processed.
10. WHEN the DataEntry_Page mounts, THE DataEntry_Page SHALL call `GET /data-entries` and display all returned entries in the history table, replacing the previous in-memory session log.
11. THE history table SHALL display columns: Month (YYYY-MM), kWh, Bill Amount (empty cell when null), Label (empty cell when null), Source, and Submitted At; and SHALL use `--font-mono` for Month, kWh, Bill Amount, and Submitted At cells.
12. IF `GET /data-entries` returns an error, THEN THE DataEntry_Page SHALL display an inline error message describing the failure and render an empty history table without crashing.
13. IF `POST /data-entries` returns an error, THEN THE DataEntry_Page SHALL display an inline error message describing the failure and retain all previously entered field values so the user can retry.

---

### Requirement 5: Persistent Chat History

**User Story:** As a user, I want my chat conversation with WATT-IF to persist across page refreshes and devices, so that I can review previous questions and answers at any time.

#### Acceptance Criteria

1. THE DB SHALL contain a `chat_history` table where each row stores a `role` value constrained to "user" or "assistant", a non-empty `text` string (max 10,000 characters), and a `created_at` ISO 8601 timestamp; rows are uniquely identified by an auto-generated integer `id`.
2. THE API SHALL expose a `GET /chat-history` endpoint that returns the most recent 100 messages from `chat_history` ordered by `created_at` ascending (oldest first) so the conversation renders in chronological order.
3. THE API SHALL expose a `POST /chat-history` endpoint that accepts a JSON body with `role` (required, "user" or "assistant") and `text` (required, 1–10,000 characters) and persists a new row, returning HTTP 422 if either constraint is violated.
4. WHEN the ChatPanel mounts, THE ChatPanel SHALL display a loading indicator in the message thread and block new question submission while `GET /chat-history` is in-flight.
5. WHEN `GET /chat-history` completes successfully, THE ChatPanel SHALL replace the loading indicator with the returned messages pre-populated in chronological order in the message thread.
6. WHEN a user submits a question and the assistant response stream completes successfully, THE ChatPanel SHALL call `POST /chat-history` first with `role` "user" and then with `role` "assistant", persisting the completed exchange in that order.
7. IF the assistant stream ends with an error, THEN THE ChatPanel SHALL NOT call `POST /chat-history` for that exchange.
8. IF `GET /chat-history` returns an error OR if the returned data cannot be rendered, THEN THE ChatPanel SHALL display both an empty message thread and an inline notice that history could not be loaded, without preventing the user from asking new questions.
9. IF the `POST /chat-history` call for the assistant message fails after the user message was already persisted, THEN THE ChatPanel SHALL log the error to the browser console, leave the partial exchange in storage without rollback, and continue normal operation without surfacing the error to the user.
10. THE ChatPanel SHALL NOT call `POST /chat-history` for messages with role "error".
