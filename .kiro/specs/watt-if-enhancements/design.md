# Design Document: WATT-IF Enhancements

## Overview

This document describes the technical design for five targeted enhancements to the WATT-IF energy intelligence web application. The changes span the React frontend, FastAPI backend, and SQLite persistence layer, and are intentionally scoped to be additive — existing functionality is preserved throughout.

The five areas are:

1. **Sidebar Branding** — Add "WATT-IF" name label below the logo in `Sidebar.tsx`
2. **Extended Forecast Horizons** — Add 9-month and 12-month options end-to-end
3. **Dashboard Temperature & Humidity** — Surface `avg_temperature` / `avg_humidity` from `ForecastMonth` in `DashboardPage` StatCards
4. **Persistent Data Entry History** — SQLite table + FastAPI endpoints + `DataEntryPage` integration
5. **Persistent Chat History** — SQLite table + FastAPI endpoints + `ChatPanel` integration

---

## Architecture

The application follows a three-tier architecture:

```
Browser (React + Vite PWA)
        │  HTTP / SSE
FastAPI server  (api/main.py + api/schemas.py)
        │  sqlite3
SQLite DB  (data/wattif.db, managed by storage/db.py)
```

All five enhancements fit within this existing architecture. No new services, build tools, or infrastructure are required. The frontend uses Vitest + fast-check for testing; the backend uses pytest.

---

## Components and Interfaces

### 1. Sidebar Branding

**File:** `frontend/src/components/Sidebar.tsx`

The `logoSectionStyle` block already uses `flexDirection: 'column'` and `alignItems: 'center'`. The current DOM is:

```
<img> (logo)
<span style={subtitleStyle}>Energy Intelligence</span>
```

The new DOM order must be:

```
<img> (logo)
<span style={nameStyle}>WATT-IF</span>
<span style={subtitleStyle}>ENERGY INTELLIGENCE</span>
```

Two new inline-style objects are added:

- `nameStyle`: `{ fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-secondary)', textAlign: 'center' }`
- `subtitleStyle` (existing, kept): `{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', letterSpacing: '0.12em', color: 'var(--color-text-muted)', textTransform: 'uppercase', textAlign: 'center' }`

The subtitle text is capitalised from "Energy Intelligence" to "ENERGY INTELLIGENCE" (CSS `text-transform: uppercase` already handles this, but the JSX string is also updated for consistency).

No other changes to `Sidebar.tsx`.

---

### 2. Extended Forecast Horizons

**Files affected:** `frontend/src/api/types.ts`, `frontend/src/components/HorizonSelector.tsx`, `frontend/src/context/ForecastContext.tsx`, `api/schemas.py`, `api/main.py`

#### TypeScript types (`types.ts`)

```typescript
// Before
export type Horizon = 1 | 3 | 6;
// After
export type Horizon = 1 | 3 | 6 | 9 | 12;

// ForecastMetadata.horizon_label
// Before: '1m' | '3m' | '6m'
// After:  '1m' | '3m' | '6m' | '9m' | '12m'
```

#### HorizonSelector

```typescript
const HORIZONS: Horizon[] = [1, 3, 6, 9, 12]
const LABELS: Record<Horizon, string> = { 1: '1m', 3: '3m', 6: '6m', 9: '9m', 12: '12m' }
```

No layout or style changes required — the existing `flex` container wraps naturally.

#### ForecastContext

The initial default `useState<Horizon>(3)` is unchanged. The `Horizon` type expansion automatically makes 9 and 12 valid values for `setHorizon`.

#### Pydantic validator (`schemas.py`)

```python
@field_validator("horizon")
@classmethod
def horizon_must_be_valid(cls, v: int) -> int:
    if v not in (1, 3, 6, 9, 12):
        raise ValueError("horizon must be 1, 3, or 6, 9, or 12")
    return v
```

#### HORIZON_LABELS (`main.py`)

```python
_HORIZON_LABELS: dict[int, str] = {1: "1m", 3: "3m", 6: "6m", 9: "9m", 12: "12m"}
```

---

### 3. Dashboard Temperature and Humidity

**Files affected:** `frontend/src/api/types.ts`, `frontend/src/pages/DashboardPage.tsx`

#### ForecastMonth interface (`types.ts`)

The backend's `pipeline/models.py` `ForecastMonth` dataclass already includes `avg_temperature` and `avg_humidity`, and the `/forecast` endpoint already serialises them. Only the frontend TypeScript interface needs updating:

```typescript
export interface ForecastMonth {
  year_month: string;
  kwh_forecast: number;
  kwh_lower_95: number;
  kwh_upper_95: number;
  price_forecast: number;
  price_lower_95: number;
  price_upper_95: number;
  avg_temperature: number;   // added
  avg_humidity: number;      // added
}
```

#### DashboardPage StatCards

Replace the static placeholder cards:

```tsx
// Before
<StatCard label="Temp Today" value="—" unit="°C" />
<StatCard label="Humidity" value="—" unit="%" />

// After
<StatCard
  label="Avg Temp"
  value={months.length > 0 && Number.isFinite(months[0].avg_temperature)
    ? months[0].avg_temperature.toFixed(1)
    : '—'}
  unit="°C"
/>
<StatCard
  label="Avg Humidity"
  value={months.length > 0 && Number.isFinite(months[0].avg_humidity)
    ? months[0].avg_humidity.toFixed(1)
    : '—'}
  unit="%"
/>
```

The four-card grid structure is preserved; only the label and value expressions change.

---

### 4. Persistent Data Entry History

**Files affected:** `storage/db.py`, `api/schemas.py`, `api/main.py`, `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/pages/DataEntryPage.tsx`

#### DB schema (`storage/db.py`)

A new DDL constant is added and appended to `_ALL_DDL`:

```python
_DDL_DATA_ENTRY_LOG = """
CREATE TABLE IF NOT EXISTS data_entry_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month   TEXT NOT NULL,
    kwh          REAL NOT NULL,
    bill_amount  REAL,
    label        TEXT,
    source       TEXT NOT NULL CHECK(source IN ('Manual', 'CSV Upload')),
    created_at   TEXT NOT NULL
);
"""
```

`init_db()` is unchanged in signature; the new DDL is executed as part of the existing loop.

#### Pydantic models (`api/schemas.py`)

```python
class DataEntryCreate(BaseModel):
    year_month: str = Field(..., description="YYYY-MM")
    kwh: float = Field(..., gt=0, le=1_000_000)
    bill_amount: float | None = Field(default=None, ge=0)
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
    id: int
    year_month: str
    kwh: float
    bill_amount: float | None
    label: str | None
    source: str
    created_at: str
```

#### API endpoints (`api/main.py`)

```python
@app.get("/data-entries", response_model=list[DataEntryRow])
async def get_data_entries() -> list[DataEntryRow]: ...

@app.post("/data-entries", response_model=DataEntryRow, status_code=201)
async def create_data_entry(body: DataEntryCreate) -> DataEntryRow: ...
```

Both use `_get_db_conn()` which already calls `init_db()`, ensuring the table exists.

#### TypeScript types and client

New types in `types.ts`:

```typescript
export interface DataEntryCreate {
  year_month: string;
  kwh: number;
  bill_amount?: number | null;
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
}
```

New functions in `client.ts`:

```typescript
export async function getDataEntries(): Promise<DataEntryRow[]>
export async function createDataEntry(entry: DataEntryCreate): Promise<DataEntryRow>
```

#### DataEntryPage redesign

The current page uses a date + time input pair and an in-memory `sessionLog`. The redesign replaces this with:

- **Form fields**: Month picker (`input[type="month"]` → `year_month`), kWh (required, `gt=0, max=1_000_000`), Bill Amount (optional, `ge=0`), Label (optional, `maxLength=100`). The date and time fields are removed.
- **State**: `historyLog: DataEntryRow[]` replaces `sessionLog: SessionLogEntry[]`. `fetchError` and `submitError` string states for inline error messages.
- **On mount**: calls `getDataEntries()`, populates `historyLog`, shows fetch error if it fails.
- **On submit**: calls `createDataEntry(...)`, prepends the new row to `historyLog`, resets form. Shows inline error if it fails, retains field values.
- **CSV upload success**: calls `createDataEntry({ year_month: currentYearMonth, kwh: 0, label: filename, source: 'CSV Upload' })` — note: the spec says to post the filename as label; `kwh` is not available from the upload response so a sentinel or the actual value from `rows_received` must be used. Since the upload response contains row counts but not kWh values, the implementation will record `kwh: 0` with a note in the label, or alternatively omit the CSV auto-log and only log manual entries. Per requirement 4.9, this should only fire when `rows_received > 0`.
- **History table columns**: Month, kWh, Bill Amount, Label, Source, Submitted At — with `--font-mono` on Month, kWh, Bill Amount, and Submitted At cells.

---

### 5. Persistent Chat History

**Files affected:** `storage/db.py`, `api/schemas.py`, `api/main.py`, `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/components/ChatPanel.tsx`

#### DB schema (`storage/db.py`)

```python
_DDL_CHAT_HISTORY = """
CREATE TABLE IF NOT EXISTS chat_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    text       TEXT NOT NULL CHECK(length(text) >= 1 AND length(text) <= 10000),
    created_at TEXT NOT NULL
);
"""
```

#### Pydantic models (`api/schemas.py`)

```python
class ChatMessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(..., min_length=1, max_length=10_000)

class ChatMessageRow(BaseModel):
    id: int
    role: str
    text: str
    created_at: str
```

#### API endpoints (`api/main.py`)

```python
@app.get("/chat-history", response_model=list[ChatMessageRow])
async def get_chat_history() -> list[ChatMessageRow]: ...
# Returns the 100 most recent rows ordered by created_at ASC

@app.post("/chat-history", response_model=ChatMessageRow, status_code=201)
async def create_chat_message(body: ChatMessageCreate) -> ChatMessageRow: ...
```

#### TypeScript types and client

```typescript
export interface ChatMessageCreate { role: 'user' | 'assistant'; text: string }
export interface ChatMessageRow { id: number; role: string; text: string; created_at: string }
```

```typescript
export async function getChatHistory(): Promise<ChatMessageRow[]>
export async function createChatMessage(msg: ChatMessageCreate): Promise<ChatMessageRow>
```

#### ChatPanel redesign

The current `ChatPanel` initialises with an empty `messages` array. The redesign adds:

- **On mount**: fetch `GET /chat-history`. While in-flight, show a loading indicator in the thread and disable the submit button. On success, map `ChatMessageRow[]` → `Message[]` (role "user" | "assistant") and pre-populate `messages`. On failure, keep `messages` empty and show an inline notice that history could not be loaded; input remains enabled.
- **After successful stream**: call `createChatMessage({ role: 'user', text: q })` then `createChatMessage({ role: 'assistant', text: accumulated })` in sequence. If the assistant POST fails, log to `console.error` and continue silently (the user message remains in storage as a partial exchange, per requirement 5.9).
- **On stream error**: do not call `createChatMessage` at all (requirement 5.7, 5.10).
- **Error-role messages** are local only and never persisted.

---

## Data Models

### `data_entry_log`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `year_month` | TEXT | NOT NULL, format YYYY-MM |
| `kwh` | REAL | NOT NULL |
| `bill_amount` | REAL | nullable |
| `label` | TEXT | nullable |
| `source` | TEXT | NOT NULL, CHECK IN ('Manual','CSV Upload') |
| `created_at` | TEXT | NOT NULL, ISO 8601 |

### `chat_history`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `role` | TEXT | NOT NULL, CHECK IN ('user','assistant') |
| `text` | TEXT | NOT NULL, length 1–10,000 |
| `created_at` | TEXT | NOT NULL, ISO 8601 |

### Updated `ForecastMonth` (frontend)

Adds `avg_temperature: number` and `avg_humidity: number` to the existing TypeScript interface, mirroring the already-present Python dataclass fields.

### Updated `Horizon` type

`1 | 3 | 6` → `1 | 3 | 6 | 9 | 12`

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: HorizonSelector button-callback fidelity

*For any* horizon value h in `{1, 3, 6, 9, 12}`, rendering `HorizonSelector` and clicking the button labelled `${h}m` SHALL invoke the `onChange` callback with exactly the value `h`.

**Validates: Requirements 2.2**

---

### Property 2: ForecastContext stores any valid horizon

*For any* horizon value h in `{1, 3, 6, 9, 12}`, calling `setHorizon(h)` within `ForecastProvider` SHALL result in the context's `horizon` field equalling `h`.

**Validates: Requirements 2.3**

---

### Property 3: ForecastRequest rejects all invalid horizons

*For any* integer v not in `{1, 3, 6, 9, 12}`, instantiating `ForecastRequest(horizon=v)` SHALL raise a `ValidationError` whose message references the invalid horizon value.

**Validates: Requirements 2.5**

---

### Property 4: Dashboard renders avg_temperature to one decimal place

*For any* finite number `t`, when `DashboardPage` is rendered with `months[0].avg_temperature = t`, the "Avg Temp" StatCard SHALL display `t.toFixed(1)`.

**Validates: Requirements 3.2**

---

### Property 5: Dashboard renders avg_humidity to one decimal place

*For any* finite number `h`, when `DashboardPage` is rendered with `months[0].avg_humidity = h`, the "Avg Humidity" StatCard SHALL display `h.toFixed(1)`.

**Validates: Requirements 3.3**

---

### Property 6: Dashboard stat grid always renders exactly four StatCards

*For any* `months` array (empty, single-element, or multi-element, with finite or non-finite weather fields), `DashboardPage` SHALL render exactly four StatCards in the stat grid without crashing.

**Validates: Requirements 3.4, 3.5**

---

### Property 7: GET /data-entries always returns rows sorted descending by created_at

*For any* set of rows inserted into `data_entry_log` with distinct `created_at` values, `GET /data-entries` SHALL return all rows ordered strictly by `created_at` descending.

**Validates: Requirements 4.2**

---

### Property 8: POST /data-entries round-trip persistence

*For any* valid `(year_month, kwh, source)` tuple, submitting it via `POST /data-entries` and then calling `GET /data-entries` SHALL result in a response that contains a row with matching `year_month`, `kwh`, and `source` values.

**Validates: Requirements 4.3**

---

### Property 9: POST /data-entries rejects invalid year_month

*For any* string `s` that does not match `\d{4}-(0[1-9]|1[0-2])` (or is absent), `POST /data-entries` with `year_month=s` SHALL return HTTP 422 with a message identifying `year_month`.

**Validates: Requirements 4.4**

---

### Property 10: POST /data-entries rejects invalid kwh

*For any* kwh value that is missing, zero, negative, or greater than 1,000,000, `POST /data-entries` SHALL return HTTP 422 identifying the `kwh` constraint violated.

**Validates: Requirements 4.5**

---

### Property 11: POST /data-entries rejects invalid source

*For any* string not in `{"Manual", "CSV Upload"}` (or absent), `POST /data-entries` with that `source` value SHALL return HTTP 422 identifying the `source` constraint violated.

**Validates: Requirements 4.6**

---

### Property 12: DataEntryPage history table displays all fetched entries

*For any* array of `DataEntryRow` objects returned by a mocked `GET /data-entries`, `DataEntryPage` SHALL render a table row for every entry in the array.

**Validates: Requirements 4.10**

---

### Property 13: GET /chat-history returns at most 100 messages ordered ascending

*For any* set of rows in `chat_history` (including sets larger than 100), `GET /chat-history` SHALL return at most 100 rows ordered by `created_at` ascending.

**Validates: Requirements 5.2**

---

### Property 14: POST /chat-history rejects invalid role or out-of-bound text

*For any* `role` value not in `{"user", "assistant"}`, or any `text` with length outside `[1, 10000]`, `POST /chat-history` SHALL return HTTP 422.

**Validates: Requirements 5.3**

---

### Property 15: ChatPanel persists every successful exchange in order

*For any* non-empty question string `q` and non-empty assistant response string `a`, after a successful stream completes, `POST /chat-history` SHALL be called exactly twice — first with `{role: "user", text: q}` and then with `{role: "assistant", text: a}` — in that order.

**Validates: Requirements 5.6**

---

### Property 16: ChatPanel never persists failed exchanges

*For any* scenario in which the assistant stream terminates with an error, `POST /chat-history` SHALL not be called for that exchange (neither for the user message nor the assistant message).

**Validates: Requirements 5.7, 5.10**

---

## Error Handling

### Frontend

| Scenario | Handling |
|---|---|
| `GET /data-entries` fails on mount | Inline error message; table rendered empty; no crash |
| `POST /data-entries` fails on submit | Inline error message; field values retained for retry |
| `GET /chat-history` fails on mount | Empty thread + inline notice; input enabled immediately |
| `POST /chat-history` (assistant) fails | `console.error` only; no UI disruption; partial exchange stays in DB |
| `months` array empty or weather fields non-finite | StatCards show "—" safely |

### Backend

| Scenario | HTTP Status | Detail |
|---|---|---|
| Invalid `horizon` in `POST /forecast` | 422 | "horizon must be 1, 3, 6, 9, or 12" |
| Missing/invalid `year_month` in `POST /data-entries` | 422 | field-level validation message |
| Invalid `kwh` in `POST /data-entries` | 422 | field-level validation message |
| Invalid `source` in `POST /data-entries` | 422 | field-level validation message |
| Invalid `role` or `text` in `POST /chat-history` | 422 | field-level validation message |
| DB connection failure | 500 | generic internal error (via global exception handler) |

Pydantic's built-in field validators produce structured 422 responses automatically; the `@field_validator` on `year_month` and the `ForecastRequest.horizon` validator produce human-readable messages that identify the violated constraint.

---

## Testing Strategy

The project uses **Vitest** + **fast-check** on the frontend and **pytest** on the backend. Both are already present in `package.json` and the Python environment.

### Unit Tests (Example-Based)

- `Sidebar.tsx`: renders "WATT-IF" label and "ENERGY INTELLIGENCE" subtitle with correct styles; all existing nav items, HealthIndicator, ModelStatusPill, and Settings link still present.
- `HorizonSelector.tsx`: renders exactly 5 buttons with correct labels in order.
- `DataEntryPage.tsx`: form contains Month picker, kWh, Bill Amount, Label fields; column headers present; mono-font cells; GET error shows inline error; POST error retains field values; CSV upload with `rows_received > 0` fires POST.
- `ChatPanel.tsx`: loading indicator shown while GET /chat-history in-flight; submit disabled during load; GET error shows inline notice with input still enabled.
- `ForecastRequest` Pydantic: horizons 9 and 12 accepted without error.
- `_HORIZON_LABELS`: equals `{1:"1m",3:"3m",6:"6m",9:"9m",12:"12m"}` exactly.
- `data_entry_log` schema: table and columns exist after `init_db`.
- `chat_history` schema: table and columns exist after `init_db`.

### Property-Based Tests (fast-check on frontend, hypothesis or fast-check equivalents on backend)

Each test runs a **minimum of 100 iterations**. Tests are tagged with:
`// Feature: watt-if-enhancements, Property N: <property_text>`

| Property | Library | What varies |
|---|---|---|
| P1 – HorizonSelector callback fidelity | fast-check (`constantFrom`) | h drawn from {1,3,6,9,12} |
| P2 – ForecastContext stores valid horizon | fast-check (`constantFrom`) | h drawn from {1,3,6,9,12} |
| P3 – ForecastRequest rejects invalid horizons | pytest + hypothesis (`integers().filter(...)`) | any integer not in {1,3,6,9,12} |
| P4 – Dashboard avg_temperature display | fast-check (`float({min:-100,max:100})`) | finite float t |
| P5 – Dashboard avg_humidity display | fast-check (`float({min:0,max:100})`) | finite float h |
| P6 – Dashboard always 4 StatCards | fast-check (arbitrary months arrays) | months array shape and values |
| P7 – GET /data-entries descending order | pytest + hypothesis (list of entries) | arbitrary entry sets with varying timestamps |
| P8 – POST /data-entries round-trip | pytest + hypothesis (valid tuples) | valid (year_month, kwh, source) values |
| P9 – POST /data-entries rejects bad year_month | pytest + hypothesis (invalid strings) | strings not matching YYYY-MM |
| P10 – POST /data-entries rejects bad kwh | pytest + hypothesis | kwh ≤ 0 or > 1,000,000 |
| P11 – POST /data-entries rejects bad source | pytest + hypothesis | strings not in {"Manual","CSV Upload"} |
| P12 – DataEntryPage displays all fetched entries | fast-check (arrays of DataEntryRow) | arbitrary-length entry arrays |
| P13 – GET /chat-history limit and order | pytest + hypothesis (lists > 100 messages) | message count, timestamps |
| P14 – POST /chat-history rejects invalid input | pytest + hypothesis | invalid role strings, out-of-bound text lengths |
| P15 – ChatPanel persists exchange in order | fast-check (question/answer strings) | question and answer content |
| P16 – ChatPanel never persists failed exchanges | fast-check (stream error scenarios) | any error message or error type |

### Integration Tests

- End-to-end: POST /forecast with horizon=9 returns 9 ForecastMonth objects; with horizon=12 returns 12.
- End-to-end: POST then GET /data-entries returns correct row in list.
- End-to-end: POST then GET /chat-history returns correct message in list.
