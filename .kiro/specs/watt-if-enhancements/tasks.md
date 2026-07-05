# Implementation Plan: WATT-IF Enhancements

## Overview

Five targeted enhancements are implemented in sequence, each building on shared type updates made early.
The plan touches the React frontend (TypeScript/TSX), the FastAPI backend (Python), and the SQLite
persistence layer. Existing functionality is preserved throughout.

Testing uses **Vitest + fast-check** on the frontend and **pytest + hypothesis** on the backend.
All 16 correctness properties defined in the design document have a corresponding property-based test task.

---

## Tasks

- [x] 1. Update shared TypeScript types (types.ts)
  - Expand the `Horizon` type union from `1 | 3 | 6` to `1 | 3 | 6 | 9 | 12`
  - Update `ForecastMetadata.horizon_label` union to include `'9m' | '12m'`
  - Add `avg_temperature: number` and `avg_humidity: number` fields to the `ForecastMonth` interface
  - Add `DataEntryCreate` and `DataEntryRow` interfaces
  - Add `ChatMessageCreate` and `ChatMessageRow` interfaces
  - _Requirements: 2.7, 2.8, 3.1, 4.1 (types), 5.1 (types)_

- [x] 2. Enhancement 1 — Sidebar Branding
  - [x] 2.1 Add "WATT-IF" name label to Sidebar.tsx
    - Add `nameStyle` style obj ect: `font-sans`, `font-weight: 700`, `font-size: 1rem`, `color: var(--color-text-secondary)`, `textAlign: 'center'`
    - Insert `<span style={nameStyle}>WATT-IF</span>` between the `<img>` logo and the subtitle `<span>`
    - Update subtitle JSX text to "ENERGY INTELLIGENCE" (CSS `text-transform: uppercase` is already present)
    - No other changes to nav items, HealthIndicator, ModelStatusPill, or Settings link
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 2.2 Write unit tests for Sidebar branding
    - Assert "WATT-IF" label renders with correct inline styles (font-weight 700, font-size 1rem)
    - Assert "ENERGY INTELLIGENCE" subtitle renders
    - Assert all five nav links, HealthIndicator, ModelStatusPill, and Settings link are still present
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Enhancement 2 — Extended Forecast Horizons
  - [x] 3.1 Update HorizonSelector.tsx
    - Change `HORIZONS` array to `[1, 3, 6, 9, 12]`
    - Add `9: '9m'` and `12: '12m'` entries to `LABELS`
    - No layout or style changes needed (existing flex container wraps naturally)
    - _Requirements: 2.1_

  - [ ]* 3.2 Write property test for HorizonSelector callback fidelity (Property 1)
    - **Property 1: HorizonSelector button-callback fidelity**
    - For any h in `{1, 3, 6, 9, 12}`, clicking the button labelled `${h}m` SHALL invoke `onChange` with exactly h
    - Use `fc.constantFrom(1, 3, 6, 9, 12)` for h
    - **Validates: Requirements 2.2**

  - [ ]* 3.3 Write property test for ForecastContext stores any valid horizon (Property 2)
    - **Property 2: ForecastContext stores any valid horizon**
    - For any h in `{1, 3, 6, 9, 12}`, calling `setHorizon(h)` SHALL result in `context.horizon === h`
    - Use `fc.constantFrom(1, 3, 6, 9, 12)` for h
    - **Validates: Requirements 2.3**

  - [ ]* 3.4 Write unit tests for HorizonSelector (5 buttons, order, labels)
    - Assert exactly 5 buttons render with labels "1m", "3m", "6m", "9m", "12m" in that order
    - Assert currently selected button has `aria-pressed="true"`
    - _Requirements: 2.1_

  - [x] 3.5 Update backend horizon validator (schemas.py + main.py)
    - In `schemas.py` `ForecastRequest.horizon_must_be_valid`: change tuple to `(1, 3, 6, 9, 12)` and update error message to "horizon must be 1, 3, 6, 9, or 12"
    - In `main.py` update `_HORIZON_LABELS` dict to `{1: "1m", 3: "3m", 6: "6m", 9: "9m", 12: "12m"}`
    - _Requirements: 2.4, 2.5, 2.6_

  - [ ]* 3.6 Write property test for ForecastRequest rejects invalid horizons (Property 3)
    - **Property 3: ForecastRequest rejects all invalid horizons**
    - For any integer v not in `{1, 3, 6, 9, 12}`, `ForecastRequest(horizon=v)` SHALL raise `ValidationError`
    - Use `hypothesis` `integers().filter(lambda v: v not in {1, 3, 6, 9, 12})`
    - **Validates: Requirements 2.5**

  - [ ]* 3.7 Write unit tests for backend horizon changes
    - Assert horizons 9 and 12 are accepted by `ForecastRequest` without error
    - Assert `_HORIZON_LABELS` equals `{1:"1m",3:"3m",6:"6m",9:"9m",12:"12m"}` exactly
    - _Requirements: 2.4, 2.6_

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Enhancement 3 — Dashboard Temperature & Humidity
  - [x] 5.1 Update DashboardPage.tsx StatCards
    - Replace `<StatCard label="Temp Today" value="—" unit="°C" />` with a StatCard labelled "Avg Temp" whose `value` is `months[0].avg_temperature.toFixed(1)` when finite, otherwise `"—"`
    - Replace `<StatCard label="Humidity" value="—" unit="%" />` with a StatCard labelled "Avg Humidity" whose `value` is `months[0].avg_humidity.toFixed(1)` when finite, otherwise `"—"`
    - Guard with `months.length > 0 && Number.isFinite(...)` before accessing the field
    - Keep the four-card grid structure unchanged
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

  - [ ]* 5.2 Write property test for dashboard avg_temperature display (Property 4)
    - **Property 4: Dashboard renders avg_temperature to one decimal place**
    - For any finite float `t` in `[-100, 100]`, rendering DashboardPage with `months[0].avg_temperature = t` SHALL display `t.toFixed(1)` in the "Avg Temp" StatCard
    - Use `fc.float({ min: -100, max: 100, noNaN: true, noDefaultInfinity: true })`
    - **Validates: Requirements 3.2**

  - [ ]* 5.3 Write property test for dashboard avg_humidity display (Property 5)
    - **Property 5: Dashboard renders avg_humidity to one decimal place**
    - For any finite float `h` in `[0, 100]`, rendering DashboardPage with `months[0].avg_humidity = h` SHALL display `h.toFixed(1)` in the "Avg Humidity" StatCard
    - Use `fc.float({ min: 0, max: 100, noNaN: true, noDefaultInfinity: true })`
    - **Validates: Requirements 3.3**

  - [ ]* 5.4 Write property test for dashboard always renders 4 StatCards (Property 6)
    - **Property 6: Dashboard stat grid always renders exactly four StatCards**
    - For any months array (empty, single-element, or multi-element; with finite or non-finite weather fields), DashboardPage SHALL render exactly 4 StatCards without crashing
    - Generate arbitrary months arrays including edge cases (empty arrays, non-finite temperature/humidity)
    - **Validates: Requirements 3.4, 3.5**

  - [ ]* 5.5 Write unit tests for DashboardPage temperature and humidity
    - Test that "—" is shown when `months` is empty
    - Test that "—" is shown when `avg_temperature` or `avg_humidity` is `Infinity`, `-Infinity`, or `NaN`
    - Test that correct formatted values appear when fields are finite numbers
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [x] 6. Enhancement 4 — Persistent Data Entry History (Backend)
  - [x] 6.1 Add data_entry_log DDL to storage/db.py
    - Add `_DDL_DATA_ENTRY_LOG` constant with the full `CREATE TABLE IF NOT EXISTS data_entry_log (...)` DDL
    - Include columns: `id` INTEGER PK AUTOINCREMENT, `year_month` TEXT NOT NULL, `kwh` REAL NOT NULL, `bill_amount` REAL, `label` TEXT, `source` TEXT NOT NULL CHECK IN ('Manual','CSV Upload'), `created_at` TEXT NOT NULL
    - Append `_DDL_DATA_ENTRY_LOG` to the `_ALL_DDL` list so `init_db()` creates the table automatically
    - _Requirements: 4.1_

  - [ ]* 6.2 Write unit tests for data_entry_log schema
    - Use `create_in_memory_db()` to verify the table and all columns exist after `init_db()`
    - Assert `source` CHECK constraint rejects values outside `{'Manual', 'CSV Upload'}`
    - _Requirements: 4.1_

  - [x] 6.3 Add DataEntryCreate and DataEntryRow Pydantic models to schemas.py
    - Add `DataEntryCreate`: fields `year_month` (str, required), `kwh` (float, gt=0, le=1_000_000), `bill_amount` (float | None, ge=0), `label` (str | None, max_length=100), `source` (Literal["Manual","CSV Upload"])
    - Add `@field_validator("year_month")` that validates `\d{4}-(0[1-9]|1[0-2])` regex
    - Add `DataEntryRow`: fields `id`, `year_month`, `kwh`, `bill_amount`, `label`, `source`, `created_at`
    - _Requirements: 4.3, 4.4, 4.5, 4.6_

  - [x] 6.4 Add GET /data-entries and POST /data-entries endpoints to main.py
    - `GET /data-entries` → query `data_entry_log` ordered by `created_at` DESC, return `list[DataEntryRow]`
    - `POST /data-entries` → insert row with `created_at` set to current UTC ISO 8601 timestamp, return `DataEntryRow` with HTTP 201
    - Import and use new Pydantic models; re-use `_get_db_conn()` which already calls `init_db()`
    - _Requirements: 4.2, 4.3_

  - [ ]* 6.5 Write property test for GET /data-entries descending order (Property 7)
    - **Property 7: GET /data-entries always returns rows sorted descending by created_at**
    - For any set of rows inserted with distinct `created_at` values, GET /data-entries SHALL return all rows ordered strictly by `created_at` descending
    - Use `hypothesis` to generate lists of valid entry dicts with varying ISO 8601 timestamps
    - **Validates: Requirements 4.2**

  - [ ]* 6.6 Write property test for POST /data-entries round-trip persistence (Property 8)
    - **Property 8: POST /data-entries round-trip persistence**
    - For any valid `(year_month, kwh, source)` tuple, POST then GET SHALL return a row with matching values
    - Use `hypothesis` `from_regex(r"\d{4}-(0[1-9]|1[0-2])")` for year_month, `floats(min_value=0.01, max_value=1_000_000)` for kwh, `sampled_from(["Manual","CSV Upload"])` for source
    - **Validates: Requirements 4.3**

  - [ ]* 6.7 Write property test for POST /data-entries rejects invalid year_month (Property 9)
    - **Property 9: POST /data-entries rejects invalid year_month**
    - For any string not matching `\d{4}-(0[1-9]|1[0-2])`, POST SHALL return HTTP 422 identifying `year_month`
    - Use `hypothesis` `text().filter(lambda s: not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", s))`
    - **Validates: Requirements 4.4**

  - [ ]* 6.8 Write property test for POST /data-entries rejects invalid kwh (Property 10)
    - **Property 10: POST /data-entries rejects invalid kwh**
    - For any kwh that is missing, zero, negative, or > 1,000,000, POST SHALL return HTTP 422 identifying `kwh`
    - Use `hypothesis` `one_of(just(0), floats(max_value=0.0), floats(min_value=1_000_001.0))`
    - **Validates: Requirements 4.5**

  - [ ]* 6.9 Write property test for POST /data-entries rejects invalid source (Property 11)
    - **Property 11: POST /data-entries rejects invalid source**
    - For any string not in `{"Manual","CSV Upload"}`, POST SHALL return HTTP 422 identifying `source`
    - Use `hypothesis` `text().filter(lambda s: s not in {"Manual","CSV Upload"})`
    - **Validates: Requirements 4.6**

- [x] 7. Enhancement 4 — Persistent Data Entry History (Frontend)
  - [x] 7.1 Add getDataEntries and createDataEntry to client.ts
    - Add `getDataEntries(): Promise<DataEntryRow[]>` calling `GET /data-entries`
    - Add `createDataEntry(entry: DataEntryCreate): Promise<DataEntryRow>` calling `POST /data-entries` with JSON body
    - Import and use the new types from `types.ts`
    - _Requirements: 4.2, 4.3_

  - [x] 7.2 Redesign DataEntryPage.tsx with persistent history
    - Replace `SessionLogEntry[]` state and date/time fields with `historyLog: DataEntryRow[]`, `fetchError`, and `submitError` states
    - Replace the date + time input pair with a single `input[type="month"]` field (maps to `year_month`)
    - Add optional Bill Amount (`input[type="number"]`, min 0) and retain Label field
    - On mount: call `getDataEntries()`, populate `historyLog`; on failure show `fetchError` inline and render empty table
    - On submit: call `createDataEntry(...)`, prepend returned row to `historyLog`, reset form; on failure show `submitError` inline and retain field values
    - On CSV upload success (when `rows_received > 0`): call `createDataEntry({ year_month: currentYearMonth, kwh: 0, label: filename, source: 'CSV Upload' })`
    - Update history table columns to: Month, kWh, Bill Amount, Label, Source, Submitted At; apply `--font-mono` to Month, kWh, Bill Amount, and Submitted At cells
    - _Requirements: 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 4.13_

  - [ ]* 7.3 Write property test for DataEntryPage displays all fetched entries (Property 12)
    - **Property 12: DataEntryPage history table displays all fetched entries**
    - For any array of `DataEntryRow` objects returned by a mocked GET /data-entries, DataEntryPage SHALL render a table row for every entry in the array
    - Use `fc.array(fc.record({ id: fc.integer(), year_month: fc.string(), kwh: fc.float({ min: 0.01 }), bill_amount: fc.option(fc.float({ min: 0 })), label: fc.option(fc.string()), source: fc.constantFrom('Manual','CSV Upload'), created_at: fc.string() }))` 
    - **Validates: Requirements 4.10**

  - [ ]* 7.4 Write unit tests for DataEntryPage redesign
    - Form contains month picker, kWh, Bill Amount, and Label fields
    - Column headers: Month, kWh, Bill Amount, Label, Source, Submitted At
    - `fetchError` inline message appears on GET failure; table is empty but renders without crash
    - `submitError` inline message appears on POST failure; field values are retained
    - CSV upload with `rows_received > 0` triggers `createDataEntry` with `source: 'CSV Upload'`
    - CSV upload with `rows_received === 0` does NOT trigger `createDataEntry`
    - _Requirements: 4.7, 4.8, 4.9, 4.12, 4.13_

- [ ] 8. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Enhancement 5 — Persistent Chat History (Backend)
  - [x] 9.1 Add chat_history DDL to storage/db.py
    - Add `_DDL_CHAT_HISTORY` constant with `CREATE TABLE IF NOT EXISTS chat_history (...)` DDL
    - Include columns: `id` INTEGER PK AUTOINCREMENT, `role` TEXT NOT NULL CHECK IN ('user','assistant'), `text` TEXT NOT NULL CHECK(length(text) >= 1 AND length(text) <= 10000), `created_at` TEXT NOT NULL
    - Append `_DDL_CHAT_HISTORY` to `_ALL_DDL`
    - _Requirements: 5.1_

  - [ ]* 9.2 Write unit tests for chat_history schema
    - Use `create_in_memory_db()` to verify the table and all columns exist after `init_db()`
    - Assert `role` CHECK constraint rejects values outside `{'user','assistant'}`
    - _Requirements: 5.1_

  - [x] 9.3 Add ChatMessageCreate and ChatMessageRow Pydantic models to schemas.py
    - Add `ChatMessageCreate`: fields `role` (Literal["user","assistant"]), `text` (str, min_length=1, max_length=10_000)
    - Add `ChatMessageRow`: fields `id` (int), `role` (str), `text` (str), `created_at` (str)
    - _Requirements: 5.3_

  - [x] 9.4 Add GET /chat-history and POST /chat-history endpoints to main.py
    - `GET /chat-history` → query the 100 most recent rows ordered by `created_at` ASC, return `list[ChatMessageRow]`
    - `POST /chat-history` → insert row with UTC ISO 8601 `created_at`, return `ChatMessageRow` with HTTP 201
    - Import and use the new Pydantic models; re-use `_get_db_conn()`
    - _Requirements: 5.2, 5.3_

  - [ ]* 9.5 Write property test for GET /chat-history limit and order (Property 13)
    - **Property 13: GET /chat-history returns at most 100 messages ordered ascending**
    - For any set of rows (including sets > 100), GET SHALL return at most 100 rows ordered by `created_at` ascending
    - Use `hypothesis` `lists(builds(...), min_size=0, max_size=150)` to generate varying message counts
    - **Validates: Requirements 5.2**

  - [ ]* 9.6 Write property test for POST /chat-history rejects invalid input (Property 14)
    - **Property 14: POST /chat-history rejects invalid role or out-of-bound text**
    - For any `role` not in `{"user","assistant"}`, or `text` with length outside `[1, 10000]`, POST SHALL return HTTP 422
    - Use `hypothesis` `text().filter(lambda r: r not in {"user","assistant"})` for role; `text(max_size=0)` and `text(min_size=10001)` for text
    - **Validates: Requirements 5.3**

- [x] 10. Enhancement 5 — Persistent Chat History (Frontend)
  - [x] 10.1 Add getChatHistory and createChatMessage to client.ts
    - Add `getChatHistory(): Promise<ChatMessageRow[]>` calling `GET /chat-history`
    - Add `createChatMessage(msg: ChatMessageCreate): Promise<ChatMessageRow>` calling `POST /chat-history` with JSON body
    - Import and use the new types from `types.ts`
    - _Requirements: 5.2, 5.3_

  - [x] 10.2 Redesign ChatPanel.tsx with persistent history
    - Add `historyLoading: boolean` and `historyError: string | null` states
    - On mount: set `historyLoading = true`, disable submit button, show loading indicator in the thread; call `getChatHistory()`, map rows to `Message[]` and pre-populate `messages`; on failure set `historyError` and keep `messages` empty with input still enabled
    - After a successful stream: call `createChatMessage({ role: 'user', text: q })` then `createChatMessage({ role: 'assistant', text: accumulated })` in sequence; if the assistant POST fails, call `console.error` and continue without surfacing the error to the user
    - On stream error: do NOT call `createChatMessage` at all (neither user nor assistant message)
    - Error-role messages remain local and are never persisted
    - _Requirements: 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10_

  - [ ]* 10.3 Write property test for ChatPanel persists every successful exchange in order (Property 15)
    - **Property 15: ChatPanel persists every successful exchange in order**
    - For any non-empty question `q` and non-empty assistant response `a`, after a successful stream, `createChatMessage` SHALL be called exactly twice — first with `{role:"user", text:q}` then with `{role:"assistant", text:a}` — in that order
    - Use `fc.string({ minLength: 1 })` for both `q` and `a`; mock `createChatMessage` and assert call order with `vi.fn()`
    - **Validates: Requirements 5.6**

  - [ ]* 10.4 Write property test for ChatPanel never persists failed exchanges (Property 16)
    - **Property 16: ChatPanel never persists failed exchanges**
    - For any scenario in which the assistant stream terminates with an error, `createChatMessage` SHALL not be called at all
    - Use `fc.string({ minLength: 1 })` for the error message; simulate `streamQuestion` calling `onError(errMsg)`; assert `createChatMessage` is never called
    - **Validates: Requirements 5.7, 5.10**

  - [ ]* 10.5 Write unit tests for ChatPanel redesign
    - Loading indicator shown and submit disabled while GET /chat-history is in-flight
    - On GET success: pre-populated messages render in the thread in chronological order
    - On GET failure: empty thread + inline notice rendered, input is enabled
    - Successful exchange calls `createChatMessage` twice in correct role order
    - Stream error does not call `createChatMessage`
    - Error-role messages are not passed to `createChatMessage`
    - _Requirements: 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10_

- [x] 11. Integration tests
  - [x]* 11.1 Write integration tests for extended horizons
    - POST /forecast with horizon=9 returns exactly 9 ForecastMonth objects
    - POST /forecast with horizon=12 returns exactly 12 ForecastMonth objects
    - _Requirements: 2.4_

  - [x]* 11.2 Write integration tests for data entry persistence
    - POST then GET /data-entries round-trip returns the correct row in the list
    - _Requirements: 4.3_

  - [x]* 11.3 Write integration tests for chat history persistence
    - POST then GET /chat-history returns the correct message in the list
    - _Requirements: 5.2, 5.3_

- [x] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP build
- Each task references specific requirements for full traceability
- Checkpoints at tasks 4, 8, and 12 gate the three logical phases of the work
- All 16 design correctness properties are covered by individual property-based test sub-tasks
- The design document uses TypeScript/Python throughout — no language selection step needed
- Backend property tests use `pytest-hypothesis`; frontend property tests use `fast-check` via `fc`
- `create_in_memory_db()` in `storage/db.py` is the recommended fixture for all backend DB tests
- The `_get_db_conn()` helper in `main.py` already calls `init_db()`, so new tables are created automatically on first request

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "3.1", "3.5", "5.1", "6.1", "9.1"] },
    { "id": 2, "tasks": ["2.2", "3.2", "3.3", "3.4", "3.6", "3.7", "5.2", "5.3", "5.4", "5.5", "6.2", "6.3", "9.2", "9.3"] },
    { "id": 3, "tasks": ["6.4", "9.4"] },
    { "id": 4, "tasks": ["6.5", "6.6", "6.7", "6.8", "6.9", "7.1", "9.5", "9.6"] },
    { "id": 5, "tasks": ["7.2", "10.1"] },
    { "id": 6, "tasks": ["7.3", "7.4", "10.2"] },
    { "id": 7, "tasks": ["10.3", "10.4", "10.5"] },
    { "id": 8, "tasks": ["11.1", "11.2", "11.3"] }
  ]
}
```
