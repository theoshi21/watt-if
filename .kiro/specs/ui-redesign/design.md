# Design Document — UI Redesign

## Overview

This design transforms WATT-IF from a single-page, vertically-stacked layout with inline styles into a multi-page, sidebar-navigated application backed by a formal CSS design token system. The core backend integrations (forecast, chat, upload, health, model-info) remain completely unchanged. What changes is how the frontend is structured, routed, and visually presented.

The key architectural shifts are:

- **react-router-dom v6** replaces the single-page layout with five distinct routes.
- **CSS custom properties** (`tokens.css`) replace all hardcoded colours, fonts, and shadows.
- **AppShell** (new) provides the persistent Sidebar + TopBar frame that all pages live inside.
- **ThemeContext** (new) manages dark/light mode with `localStorage` persistence.
- **Shared ForecastContext** (new) lifts forecast state so Dashboard and Forecast pages share data without prop-drilling through the shell.

### Research Summary

`react-router-dom` v6 ships `<BrowserRouter>`, `<Routes>`, `<Route>`, `<NavLink>`, and `<Outlet>` — the primitives needed for this design. `NavLink` provides an `isActive` callback and a default `.active` class, making active-link styling trivial. The `<Navigate replace>` element handles 404 redirects without leaving invalid entries in the history stack.

The focus-trap requirement (Req 18.3) is best satisfied by a small utility that enumerates focusable elements within the drawer and intercepts `Tab`/`Shift+Tab` — this avoids adding a library dependency. Alternatively, the `focus-trap-react` package (MIT, actively maintained) can be used; the tasks spec will offer both options.

`fast-check` (already a dev-dependency) is the property-based testing library used throughout.


---

## Architecture

### New File / Folder Structure

```
frontend/src/
  main.tsx                    — mounts BrowserRouter + ThemeProvider + App
  App.tsx                     — renders AppShell inside BrowserRouter
  styles/
    tokens.css                — all CSS custom properties (:root + dark override)
    index.css                 — body/global resets, button classes, card classes
  context/
    ThemeContext.tsx           — dark/light mode context + localStorage
    ForecastContext.tsx        — shared forecast state (months, loading, error)
  components/
    AppShell.tsx              — NEW: Sidebar + TopBar layout wrapper + Outlet
    Sidebar.tsx               — NEW: nav links, ModelStatusPill, HealthIndicator
    TopBar.tsx                — NEW: page h1, icon buttons, DarkModeToggle
    ModelStatusPill.tsx       — NEW: polls /model-info every 60s
    StatCard.tsx              — NEW: dl/dt/dd KPI card
    AnomalyCard.tsx           — NEW: teal-bordered alert card
    ChatPanel.tsx             — MODIFIED: token-based bubble colours
    ForecastChart.tsx         — MODIFIED: token-based chart colours
    HealthIndicator.tsx       — MODIFIED: token colours, sidebar placement
    HorizonSelector.tsx       — MODIFIED: token-based button styles
    ModelEvaluation.tsx       — MODIFIED: token migration for all hardcoded values
    OfflineBanner.tsx         — MODIFIED: token-based colour, positioning rule
    UploadPanel.tsx           — MODIFIED: primary button style class
  pages/
    DashboardPage.tsx         — NEW: / route
    ForecastPage.tsx          — NEW: /forecast route
    AskPage.tsx               — NEW: /ask route
    DataEntryPage.tsx         — NEW: /data-entry route
    RecommendationsPage.tsx   — NEW: /recommendations route
  api/
    client.ts                 — UNCHANGED
    types.ts                  — UNCHANGED
  test/
    (existing tests — updated imports as needed)
    AppShell.test.tsx         — NEW
    StatCard.test.tsx         — NEW
    DashboardPage.test.tsx    — NEW
    ForecastPage.test.tsx     — NEW
    DataEntryPage.test.tsx    — NEW
    ThemeContext.test.tsx     — NEW
```


### Routing Setup

`react-router-dom` v6 is added as a production dependency. `BrowserRouter` wraps the entire tree in `main.tsx`. `AppShell` uses `<Outlet>` to render the matched page into the content area.

```tsx
// main.tsx
<BrowserRouter>
  <ThemeProvider>
    <ForecastProvider>
      <App />
    </ForecastProvider>
  </ThemeProvider>
</BrowserRouter>

// App.tsx — route table
<Routes>
  <Route path="/" element={<AppShell />}>
    <Route index element={<DashboardPage />} />
    <Route path="forecast" element={<ForecastPage />} />
    <Route path="ask" element={<AskPage />} />
    <Route path="data-entry" element={<DataEntryPage />} />
    <Route path="recommendations" element={<RecommendationsPage />} />
    <Route path="*" element={<Navigate replace to="/" />} />
  </Route>
</Routes>
```

The `*` catch-all uses `replace` so the invalid URL is replaced rather than pushed, satisfying Req 3.4. Vite's dev server already serves `index.html` for all paths. For production the server must be configured to serve `index.html` for all 404s (standard SPA deployment).

### State Management

| State | Location | Rationale |
|---|---|---|
| `theme` (`'light' \| 'dark'`) | `ThemeContext` | Global — affects every component |
| `months`, `forecastLoading`, `forecastError`, `horizon` | `ForecastContext` | Shared between Dashboard (read) and Forecast (read+write) |
| `evalRefreshKey` | `DataEntryPage` local | Only needed to trigger ModelEvaluation re-fetch after upload |
| `sidebarOpen` | `AppShell` local | Only `AppShell` + `Sidebar` need this |
| `messages`, `input`, `loading` | `ChatPanel` local | Scoped to the Ask page |
| `sessionLog` entries | `DataEntryPage` local | Session-only, no need to share |
| `modelInfo` (for pill) | `ModelStatusPill` local | Self-contained polling component |
| `health` | `HealthIndicator` local | Self-contained polling component |


### High-Level Layout Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  OfflineBanner (sticky, z-index 1000, above shell)           │
├─────────────┬────────────────────────────────────────────────┤
│             │  TopBar (h1 + icon buttons)                    │
│  Sidebar    ├────────────────────────────────────────────────┤
│  220px      │                                                │
│  (fixed)    │  <Outlet> — page content                       │
│             │  (DashboardPage / ForecastPage / etc.)         │
│             │                                                │
│  [bottom]   │                                                │
│  StatusPill │                                                │
│  Health     │                                                │
│  Settings   │                                                │
└─────────────┴────────────────────────────────────────────────┘
```

On mobile (< 768 px) the Sidebar is hidden and slides in as an overlay drawer triggered by a hamburger button in the TopBar.

---

## Design Token System

### File: `src/styles/tokens.css`

All tokens are declared on `:root`. Dark theme overrides are declared on `[data-theme="dark"]` applied to `<html>`.

```css
:root {
  /* ── Sidebar ─────────────────────────────────────────────── */
  --color-sidebar-bg:          #0d1b2a;
  --color-sidebar-alt:         #1a2d40;

  /* ── Page / Structure ────────────────────────────────────── */
  --color-page-bg:             #f0f4f8;
  --color-card-bg:             #ffffff;
  --color-border:              #e2e8f0;
  --color-input-fill:          #f8fafc;

  /* ── Accent ──────────────────────────────────────────────── */
  --color-accent-primary:      #2563eb;
  --color-accent-hover:        #1d4ed8;
  --color-text-on-accent:      #ffffff;

  /* ── Semantic ────────────────────────────────────────────── */
  --color-teal:                #0d9488;
  --color-amber:               #f59e0b;
  --color-red:                 #dc2626;

  /* ── Text ────────────────────────────────────────────────── */
  --color-text-primary:        #0f172a;
  --color-text-muted:          #64748b;
  --color-text-secondary:      #cbd5e1;

  /* ── Rating levels ───────────────────────────────────────── */
  --color-rating-excellent-bg:     #dcfce7;
  --color-rating-excellent-border: #16a34a;
  --color-rating-excellent-text:   #15803d;

  --color-rating-good-bg:          #dbeafe;
  --color-rating-good-border:      #2563eb;
  --color-rating-good-text:        #1d4ed8;

  --color-rating-fair-bg:          #fef3c7;
  --color-rating-fair-border:      #d97706;
  --color-rating-fair-text:        #b45309;

  --color-rating-poor-bg:          #fee2e2;
  --color-rating-poor-border:      #dc2626;
  --color-rating-poor-text:        #b91c1c;

  /* ── Typography ──────────────────────────────────────────── */
  --font-sans:  'Inter', system-ui, sans-serif;
  --font-mono:  'Space Mono', monospace;

  /* ── Spacing / Shape ─────────────────────────────────────── */
  --radius-card: 0.75rem;

  /* ── Shadows ─────────────────────────────────────────────── */
  --shadow-card:    0 1px 3px rgba(0, 0, 0, 0.08), 0 4px 14px rgba(0, 0, 0, 0.04);
  --shadow-sidebar: 2px 0 12px rgba(0, 0, 0, 0.15);
}

[data-theme="dark"] {
  --color-sidebar-bg:          #050d14;
  --color-sidebar-alt:         #0d1b2a;
  --color-page-bg:             #0f172a;
  --color-card-bg:             #1e293b;
  --color-border:              #334155;
  --color-input-fill:          #1e293b;
  --color-accent-primary:      #3b82f6;
  --color-accent-hover:        #2563eb;
  --color-text-on-accent:      #ffffff;
  --color-teal:                #2dd4bf;
  --color-amber:               #fbbf24;
  --color-red:                 #f87171;
  --color-text-primary:        #f1f5f9;
  --color-text-muted:          #94a3b8;
  --color-text-secondary:      #e2e8f0;
  --color-rating-excellent-bg:     #14532d;
  --color-rating-excellent-border: #16a34a;
  --color-rating-excellent-text:   #4ade80;
  --color-rating-good-bg:          #1e3a8a;
  --color-rating-good-border:      #3b82f6;
  --color-rating-good-text:        #93c5fd;
  --color-rating-fair-bg:          #78350f;
  --color-rating-fair-border:      #f59e0b;
  --color-rating-fair-text:        #fde68a;
  --color-rating-poor-bg:          #7f1d1d;
  --color-rating-poor-border:      #f87171;
  --color-rating-poor-text:        #fca5a5;
}
```


### Google Fonts Integration (`index.html`)

```html
<!-- Preconnects must appear before the stylesheet link -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap"
/>
```

`font-display=swap` ensures text is visible immediately using the fallback stack (`system-ui, sans-serif` / `monospace`) while the web fonts load. If the request fails (offline), the fallback stack is used transparently — no layout shift because both Inter and system-ui share similar metrics.

---

## Components and Interfaces

### `ThemeContext` (new)

**File:** `src/context/ThemeContext.tsx`

```tsx
type Theme = 'light' | 'dark'

interface ThemeContextValue {
  theme: Theme
  toggleTheme: () => void
}
```

**Behaviour:**
- On mount, reads `localStorage.getItem('wattif-theme')`. If the value is `'dark'`, initialises with dark; otherwise defaults to `'light'`.
- Sets `document.documentElement.dataset.theme` on every theme change so all CSS tokens update immediately.
- Writes to `localStorage` on every toggle.
- The initial `dataset.theme` assignment happens synchronously inside the context initialiser (before first render) via a `useState` initialiser function that reads localStorage — this prevents a flash of the wrong theme.

**Tokens used:** mutates `data-theme` on `<html>`.


### `ForecastContext` (new)

**File:** `src/context/ForecastContext.tsx`

```tsx
interface ForecastContextValue {
  months: ForecastMonth[]
  horizon: Horizon
  loading: boolean
  error: string | null
  setHorizon: (h: Horizon) => void
  loadForecast: (h: Horizon) => Promise<void>
  setMonths: (m: ForecastMonth[]) => void
}
```

**Behaviour:**
- Owns `months`, `horizon`, `loading`, `error` state.
- `loadForecast` calls `getForecast(h)`, handles 503 vs other errors.
- On mount (inside the provider) auto-loads 3-month forecast if training is not running (mirrors existing App.tsx logic).
- Exposes `setMonths` so DataEntryPage can reset forecast data after upload triggers retraining.

---

### `AppShell` (new)

**File:** `src/components/AppShell.tsx`

```tsx
interface AppShellProps {
  // no external props — reads location from router
}

// Internal state
sidebarOpen: boolean  // mobile drawer state
```

**Behaviour:**
- Renders `<OfflineBanner>` above the shell grid.
- Renders a two-column CSS grid: `220px auto` (desktop) collapsing to `1fr` (mobile).
- Renders `<Sidebar>` in the left column, `<TopBar>` + `<Outlet>` in the right column.
- On mobile, `sidebarOpen` toggles a `.sidebar--open` class that slides the drawer in.
- Passes `sidebarOpen`, `onOpen`, `onClose` down to Sidebar and TopBar.
- Closes the drawer on outside-click via an `onClick` on the overlay backdrop element.
- Closes the drawer on `Escape` keydown via `useEffect` on `document`.

**Layout CSS (in `index.css`):**

```css
.app-shell {
  display: grid;
  grid-template-columns: 220px 1fr;
  grid-template-rows: auto 1fr;
  min-height: 100vh;
}
.app-shell__sidebar { grid-row: 1 / -1; }
.app-shell__main { display: flex; flex-direction: column; }

@media (max-width: 767px) {
  .app-shell { grid-template-columns: 1fr; }
  .app-shell__sidebar {
    position: fixed; top: 0; left: 0;
    width: 220px; height: 100vh; z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
  }
  .app-shell__sidebar--open { transform: translateX(0); }
  .app-shell__overlay {
    display: none; position: fixed; inset: 0; z-index: 199;
    background: rgba(0,0,0,0.4);
  }
  .app-shell__overlay--visible { display: block; }
}
```

**Tokens used:** layout only — no colour tokens directly; delegates to child components.


### `Sidebar` (new)

**File:** `src/components/Sidebar.tsx`

```tsx
interface SidebarProps {
  open: boolean        // mobile: drawer open state
  onClose: () => void  // mobile: called to close drawer
}
```

**Behaviour:**
- Renders the WATT-IF logo (`wattif.png`) + "ENERGY INTELLIGENCE" subtitle.
- Renders 5 `<NavLink>` items (Dashboard, Forecast, Ask WATT-IF, Recommendations, Data Entry) using `react-router-dom`'s `NavLink`. Each receives an `isActive` class callback that applies `.nav-item--active` when the route matches.
- Nav items render as `<NavLink>` (which renders an `<a>`) for keyboard and screen reader accessibility.
- Renders `<HealthIndicator>` below the nav list.
- Renders `<ModelStatusPill>` above the Settings link.
- Renders a Settings `<a>` at the very bottom (no route in this release, `href="#"`).
- When `open` is true and drawer is active, focus is moved to the first nav link on open.
- Each nav icon is a simple inline SVG (or from a small icon set — see Implementation Notes).

**Tokens used:** `--color-sidebar-bg`, `--color-sidebar-alt`, `--shadow-sidebar`, `--color-accent-primary`, `--color-text-secondary`, `--color-text-muted`, `--color-text-primary`.

**Nav item active style:**
```css
.nav-item--active {
  background: var(--color-accent-primary);
  color: var(--color-text-secondary);
}
```

---

### `TopBar` (new)

**File:** `src/components/TopBar.tsx`

```tsx
interface TopBarProps {
  onMenuClick: () => void   // mobile: open sidebar drawer
}
```

**Behaviour:**
- Reads current route via `useLocation()` and maps it to a page title string.
- Renders the page title as `<h1>`.
- Renders hamburger `<button>` (visible only on mobile via CSS).
- Renders three icon buttons on the right: `DarkModeToggle`, notifications bell, user avatar.
- Notifications and avatar buttons are accessible `<button>` elements with `aria-label` but no action.

**Page title mapping:**
```
/            → "Dashboard"
/forecast    → "Forecast"
/ask         → "Ask WATT-IF"
/data-entry  → "Data Entry"
/recommendations → "Recommendations"
```

**Tokens used:** `--color-card-bg`, `--color-border`, `--color-text-primary`, `--color-accent-primary`, `--font-sans`.

---

### `ModelStatusPill` (new)

**File:** `src/components/ModelStatusPill.tsx`

```tsx
// No external props

// Internal state
modelInfo: ModelInfoResponse | null
loading: boolean
```

**Behaviour:**
- On mount, calls `getModelInfo()` and sets a 60-second interval to repeat.
- Cleans up interval on unmount.
- If `mape_avg_pct` is non-null: displays green pill "MODEL ACTIVE · MAPE X.X%".
- If loading, null `mape_avg_pct`, or error: displays "MODEL NOT TRAINED" with `--color-text-muted` styling.

**Tokens used:** `--color-teal`, `--color-text-muted`, `--font-mono`, `--color-sidebar-bg`.


### `StatCard` (new)

**File:** `src/components/StatCard.tsx`

```tsx
interface StatCardProps {
  label: string
  value: string | number
  unit?: string
}
```

**Behaviour:**
- Renders a `<dl>` containing a `<dt>` for the label and a `<dd>` for the value (with optional unit appended).
- Value text uses `--font-mono`; label text uses `--font-sans`.
- Applies card token styles (`--color-card-bg`, `--color-border`, `--radius-card`, `--shadow-card`).

**Tokens used:** `--font-mono`, `--font-sans`, `--color-card-bg`, `--color-border`, `--radius-card`, `--shadow-card`, `--color-text-primary`, `--color-text-muted`.

---

### `AnomalyCard` (new)

**File:** `src/components/AnomalyCard.tsx`

```tsx
interface AnomalyCardProps {
  month: string       // formatted year-month label e.g. "Jan 2025"
  percentAbove: number  // percentage excess rounded to 1 decimal
}
```

**Behaviour:**
- Renders a card with a 4 px left border using `--color-teal`.
- Displays the anomaly message: "Anomaly Detected: forecast consumption for [month] is [X.X]% above your average."
- Applies standard card tokens.

**Tokens used:** `--color-teal`, `--color-card-bg`, `--color-border`, `--radius-card`, `--shadow-card`, `--color-amber` (icon accent), `--color-text-primary`.

---

### `DashboardPage` (new)

**File:** `src/pages/DashboardPage.tsx`

**State:** Reads `months`, `loading`, `error` from `ForecastContext`.

**Behaviour:**
- If `loading`: renders loading skeleton (4 placeholder cards + chart placeholder).
- If `months.length === 0` and not loading and no error: renders empty-state prompt card.
- Otherwise: renders StatCard grid (4 cards), then `ForecastChart` (3-month data), then optionally `AnomalyCard`.
- Anomaly detection logic: `months[0].kwh_forecast > 1.1 × mean(months.map(m => m.kwh_forecast))`.
- StatCard values:
  - "This Month kWh" → `months[0].kwh_forecast.toFixed(2)`
  - "Daily Average kWh/day" → `(months[0].kwh_forecast / 30).toFixed(2)`
  - "Temp Today °C" → `"—"` (placeholder)
  - "Humidity %" → `"—"` (placeholder)

**Tokens used:** `--color-page-bg`, card tokens, `--font-sans`.

---

### `ForecastPage` (new)

**File:** `src/pages/ForecastPage.tsx`

**State:** Reads and writes `months`, `horizon`, `loading`, `error`, `loadForecast`, `setHorizon` from `ForecastContext`.

**Behaviour:**
- On mount: if no months loaded, calls `loadForecast(3)`.
- Renders `HorizonSelector` (disabled while loading) + `ForecastChart`.
- While loading: renders `<span role="status">Loading…</span>`.
- On 503 error: renders message in `<p role="alert">`.
- On other error: renders human-readable message in `<p role="alert">`.

---

### `AskPage` (new)

**File:** `src/pages/AskPage.tsx`

**Behaviour:** Renders `<ChatPanel>` inside a wrapper that fills the remaining viewport height below the TopBar.

---

### `DataEntryPage` (new)

**File:** `src/pages/DataEntryPage.tsx`

```tsx
interface SessionLogEntry {
  date: string
  time: string
  kwh: string
  label: string
  source: 'Manual' | 'CSV Upload'
}
```

**Internal state:** `sessionLog: SessionLogEntry[]`, form field state, validation errors state.

**Behaviour:**
- New Reading form: date (required), time (required), kwh number (required, min 0, max 999999), label text (optional, maxLength 100).
- On valid submit: appends to `sessionLog`, resets all fields.
- On invalid submit: sets per-field error messages, does NOT append.
- `UploadPanel` `onUploadSuccess` callback: appends a CSV Upload row with current timestamp, `kwh: "—"`, label = filename.
- SessionLog table: empty state if `sessionLog.length === 0`.
- Date/Time/kWh cells use `--font-mono`.

---

### `RecommendationsPage` (new)

**File:** `src/pages/RecommendationsPage.tsx`

**Behaviour:** Renders a single card with heading "Recommendations" and body text as specified in Req 11.1. Uses all standard card tokens.


### Modified Components

#### `ChatPanel` (modified)

Replace all hardcoded hex values with CSS variable references:

| Hardcoded | Token |
|---|---|
| `#3a7bd5` (user bubble bg) | `var(--color-accent-primary)` |
| `#fff` (user bubble text) | `var(--color-text-on-accent)` |
| `#ffffff` (assistant bubble bg) | `var(--color-card-bg)` |
| `1px solid #e8e8e8` | `1px solid var(--color-border)` |
| `#222` (assistant text) | `var(--color-text-primary)` |
| `#ffebee` (error bubble bg) | light red via `--color-red` at opacity |
| `#c62828` (error text) | `var(--color-red)` |
| `#fafafa` (thread bg) | `var(--color-input-fill)` |
| Submit button bg (`#3a7bd5`) | `var(--color-accent-primary)` |
| Submit button disabled (`#aaa`) | `var(--color-text-muted)` |
| Input border (`#ccc`) | `var(--color-border)` |
| Input bg | `var(--color-input-fill)` |

#### `ForecastChart` (modified)

The hardcoded `colors` object is replaced with CSS variable references. Since Recharts `stroke`/`fill` props accept CSS variable strings:

| Old constant | Token |
|---|---|
| `colors.kwh` (`#1d4ed8`) | `var(--color-accent-primary)` |
| `colors.price` (`#c2410c`) | `var(--color-red)` |
| `colors.grid` (`#d1d5db`) | `var(--color-border)` |
| `colors.text` (`#111827`) | `var(--color-text-primary)` |
| `colors.muted` (`#4b5563`) | `var(--color-text-muted)` |
| `colors.card` (`#ffffff`) | `var(--color-card-bg)` |
| `colors.background` (`#f9fafb`) | `var(--color-page-bg)` |

`chartCardStyle` migrates `background`, `border`, `borderRadius`, `boxShadow` to tokens.

**Note:** Recharts axis tick `fill` and `stroke` attributes accept `var()` references; verified as working in Recharts 2.x.

#### `HorizonSelector` (modified)

Active button: `background: var(--color-accent-primary)`, `color: var(--color-text-on-accent)`, `border: 2px solid var(--color-accent-primary)`.
Inactive button: `background: var(--color-input-fill)`, `color: var(--color-text-primary)`, `border: 2px solid var(--color-border)`.
Disabled: `cursor: not-allowed`.
Border-radius: `var(--radius-card)`.

#### `HealthIndicator` (modified)

Replace hardcoded colours with tokens and update text:
- `'connecting'` state → "Connecting…" text using `--color-text-muted`.
- `'unreachable'` state → "Backend offline" text using `--color-red`.
- Dot colours: operational → `--color-teal`, degraded → `--color-amber`.
- All-operational state: single dot + "All systems operational" in `--color-teal`.
- Remove the `last_upload_at` / `model_trained_at` display lines (that info is available elsewhere; sidebar space is constrained).
- The component is now rendered inside `Sidebar`, not in App/header.

#### `ModelEvaluation` (modified)

- Replace all `RATING_COLOR`/`RATING_BG` maps with CSS variable references: `.rating-badge--excellent`, `.rating-badge--good`, `.rating-badge--fair`, `.rating-badge--poor` classes that use the `--color-rating-*` tokens.
- All metric numeric values wrapped in `<span style={{ fontFamily: 'var(--font-mono)' }}>` (or a CSS class).
- All `background`, `border`, and colour styles replaced with token references.

#### `OfflineBanner` (modified)

Replace `background: '#ff9800'` with `background: var(--color-accent-primary)` and add `color: var(--color-sidebar-bg)`.

#### `UploadPanel` (modified)

Replace label/button inline styles with `.btn-primary` CSS class.


---

## Data Models

No new backend API types are introduced. The existing types in `src/api/types.ts` are unchanged. New frontend-only models:

```ts
// ThemeContext
type Theme = 'light' | 'dark'
const THEME_STORAGE_KEY = 'wattif-theme'

// DataEntryPage
interface SessionLogEntry {
  date: string       // 'YYYY-MM-DD'
  time: string       // 'HH:MM'
  kwh: string        // formatted number or '—'
  label: string      // user label or filename
  source: 'Manual' | 'CSV Upload'
}

// DashboardPage anomaly check (pure function)
function detectAnomaly(months: ForecastMonth[]): {
  detected: boolean
  monthLabel: string
  percentAbove: number
} | null

// AnomalyCard props
interface AnomalyCardProps {
  month: string
  percentAbove: number
}

// StatCard props
interface StatCardProps {
  label: string
  value: string | number
  unit?: string
}
```

The anomaly detection function is a pure computation easily covered by property tests:

```ts
function detectAnomaly(months: ForecastMonth[]) {
  if (months.length < 2) return null
  const mean = months.reduce((s, m) => s + m.kwh_forecast, 0) / months.length
  const first = months[0].kwh_forecast
  if (first > mean * 1.1) {
    return {
      detected: true,
      monthLabel: formatMonth(months[0].year_month),
      percentAbove: ((first - mean) / mean) * 100,
    }
  }
  return null
}
```

---

## Routing and Navigation

### Route Table

| Path | Component | Page Title |
|---|---|---|
| `/` | `DashboardPage` | Dashboard |
| `/forecast` | `ForecastPage` | Forecast |
| `/ask` | `AskPage` | Ask WATT-IF |
| `/data-entry` | `DataEntryPage` | Data Entry |
| `/recommendations` | `RecommendationsPage` | Recommendations |
| `*` (catch-all) | `<Navigate replace to="/" />` | — |

### NavLink Active Class Strategy

`react-router-dom`'s `NavLink` receives a class callback:

```tsx
<NavLink
  to={path}
  className={({ isActive }) =>
    isActive ? 'nav-item nav-item--active' : 'nav-item'
  }
  end={path === '/'}  // exact match only for root
>
```

The `end` prop is required for `/` so that sub-paths like `/forecast` don't also activate the Dashboard link.

### 404 Redirect

```tsx
<Route path="*" element={<Navigate replace to="/" />} />
```

Using `replace` ensures the invalid URL does not appear in `window.history`.

### Deep Link / Direct URL Loading

Vite dev server handles this automatically (`historyApiFallback` equivalent). For production, the server (nginx / Vite preview) must serve `index.html` for all non-asset 404s. The `vite.config.ts` requires no changes for this — it is a deployment concern documented in the implementation notes.


---

## CSS Architecture

### File Organization

| File | Purpose |
|---|---|
| `src/styles/tokens.css` | All CSS custom properties (`:root` + `[data-theme="dark"]`) |
| `src/styles/index.css` | Body reset, `.btn-primary`, `.btn-secondary`, `.card`, responsive grid, font assignment |
| Component inline styles | Only structural (display, flex, padding) — never colour literals |

Components use `style={{ ... }}` with `var(--token)` values or CSS classes from `index.css`. CSS Modules are not introduced to keep the migration scope minimal.

### Global `index.css` (key classes)

```css
body {
  font-family: var(--font-sans);
  background: var(--color-page-bg);
  color: var(--color-text-primary);
  margin: 0;
}

/* Card */
.card {
  background: var(--color-card-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 1.25rem;
}

/* Primary button */
.btn-primary {
  background: var(--color-accent-primary);
  color: var(--color-text-on-accent);
  border: none;
  border-radius: var(--radius-card);
  font-family: var(--font-sans);
  font-size: 0.9rem;
  font-weight: 500;
  padding: 0.5rem 1.1rem;
  cursor: pointer;
  transition: background 0.15s ease;
}
.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
}
.btn-primary:focus-visible {
  outline: 2px solid var(--color-accent-hover);
  outline-offset: 2px;
}
.btn-primary:disabled {
  background: var(--color-text-muted);
  cursor: not-allowed;
}

/* Secondary / outlined button */
.btn-secondary {
  background: transparent;
  color: var(--color-accent-primary);
  border: 1px solid var(--color-accent-primary);
  border-radius: var(--radius-card);
  font-family: var(--font-sans);
  font-size: 0.9rem;
  font-weight: 500;
  padding: 0.5rem 1.1rem;
  cursor: pointer;
}
.btn-secondary:hover:not(:disabled) {
  background: var(--color-accent-primary);
  color: var(--color-text-on-accent);
}
.btn-secondary:disabled {
  border-color: var(--color-text-muted);
  color: var(--color-text-muted);
  cursor: not-allowed;
}
```

### Responsive Breakpoints

| Breakpoint | Value | Effect |
|---|---|---|
| Mobile breakpoint | `max-width: 767px` | Hide sidebar, show hamburger, StatCard 2-col |
| Small mobile | `max-width: 479px` | StatCard 1-col |

### StatCard Grid

```css
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}
@media (max-width: 767px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 479px) {
  .stat-grid { grid-template-columns: 1fr; }
}
```


---

## Mobile / Responsive Strategy

### Hamburger Menu

The hamburger button lives in `TopBar` and is only visible via CSS at `max-width: 767px`. Clicking it calls `onMenuClick()` which sets `sidebarOpen = true` in `AppShell`.

### Overlay Drawer

When `sidebarOpen` is true, a semi-transparent backdrop `<div class="app-shell__overlay app-shell__overlay--visible">` is rendered behind the sidebar (z-index 199). Clicking the backdrop calls `onClose()`. The sidebar itself slides in via `transform: translateX(0)` from `translateX(-100%)` with a `0.25s ease` transition.

### Focus Trap

When the drawer opens, `AppShell` uses a `useEffect` to:
1. Save a reference to `document.activeElement` (the hamburger button) as `returnFocusRef`.
2. Call `focus()` on the first focusable element inside the drawer.
3. Attach a `keydown` listener to the drawer element that intercepts `Tab` and `Shift+Tab`, cycling focus within the drawer's focusable elements (queried via `querySelectorAll('a, button, input, [tabindex]:not([tabindex="-1"])')`).

When the drawer closes, focus is returned to `returnFocusRef.current` (the hamburger button).

This satisfies Req 18.2, 18.3, and 18.5 without adding a library dependency. If desired, `focus-trap-react` (MIT, well-maintained) can replace the manual implementation.

### ForecastChart Overflow Prevention

`ForecastChart`'s `<ResponsiveContainer width="100%">` already prevents horizontal overflow. A CSS rule ensures minimum height on mobile:

```css
@media (max-width: 767px) {
  .recharts-responsive-container { min-height: 240px; }
}
```

---

## Accessibility Implementation

### Keyboard Navigation

- All nav items are `<NavLink>` (renders `<a>`) — inherently keyboard focusable.
- All interactive elements (buttons, inputs) are native HTML elements.
- `HorizonSelector` already uses `<button>` elements.
- Icon buttons in TopBar use `<button>` with `aria-label`.

### Focus Management for Mobile Drawer

As described in the Responsive Strategy section: open → focus first nav item; close → return focus to hamburger button.

### ARIA Labels

| Element | `aria-label` value |
|---|---|
| DarkModeToggle button | `"Toggle dark mode"` |
| Notifications button | `"Notifications"` |
| Avatar button | `"User account"` |
| Hamburger button | `"Open navigation menu"` |
| Sidebar (nav element) | `"Main navigation"` |
| Chat message log | `"Conversation"` (existing) |
| HealthIndicator aside | `"System health"` (existing) |

### StatCard Semantic Markup

```tsx
<dl className="stat-card">
  <dt style={{ fontFamily: 'var(--font-sans)', color: 'var(--color-text-muted)' }}>
    {label}
  </dt>
  <dd style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)' }}>
    {value}{unit ? <span> {unit}</span> : null}
  </dd>
</dl>
```

Screen readers will announce `<dt>`/`<dd>` pairs as term/definition, meeting Req 18.6.

### Colour Contrast

The token values are chosen to meet WCAG 2.1 AA:
- `--color-text-primary` (`#0f172a`) on `--color-card-bg` (`#ffffff`) → ratio ~18.5:1 ✓
- `--color-text-on-accent` (`#ffffff`) on `--color-accent-primary` (`#2563eb`) → ratio ~5.9:1 ✓
- `--color-text-muted` (`#64748b`) on `--color-card-bg` (`#ffffff`) → ratio ~4.6:1 ✓
- Dark theme values maintain equivalent or better ratios.

Full WCAG AA validation requires manual testing with assistive technologies and expert accessibility review.


---

## Error Handling

| Scenario | Component | Handling |
|---|---|---|
| Forecast 503 | `ForecastPage` / `ForecastContext` | Clear months, render "No trained model" in `role="alert"` |
| Forecast network error | `ForecastPage` / `ForecastContext` | Clear months, render human-readable error in `role="alert"` |
| `/model-info` error | `ModelStatusPill` | Display "MODEL NOT TRAINED" — no error message exposed to user |
| `/model-info` error | `ModelEvaluation` | Existing `role="alert"` error paragraph |
| `/health` unreachable | `HealthIndicator` | Display "Backend offline" in `--color-red` |
| Google Fonts load failure | `index.html` | System font fallback renders text immediately |
| CSV validation error | `UploadPanel` | Existing `role="alert"` status span (no change to logic) |
| Form validation | `DataEntryPage` | Inline per-field error messages, no submit |
| Unknown route | `react-router-dom` | `<Navigate replace to="/" />` |

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

The property-based testing library used is **`fast-check`** (already installed as a dev dependency). Each property test is configured to run a minimum of 100 iterations.

#### Reflection: Eliminating Redundancy

Before listing final properties, redundancy is assessed:

- Properties about "StatCard uses dl/dt/dd" (Req 7.6) and "StatCard accessible markup" (Req 18.6) are equivalent — combined into Property 4.
- Properties about "card tokens applied to each component" (Req 12.1) and "button token invariant" (Req 13.1/13.6) are distinct — kept separate.
- "ChatPanel message role → token colour" properties for user/assistant/error (Req 9.2-9.4) can be combined into a single parametric property.
- "SessionLog grows by 1 on valid submit" (Req 10.2) and "SessionLog uses font-mono" (Req 10.7) are distinct properties.
- The "HorizonSelector active button" property (Req 8.7) and "nav item active state" property (Req 5.3) are structurally similar but test different components — kept separate.
- "AppShell renders shell on all routes" (Req 4.1) and "nav item active for current route" (Req 5.3) are distinct.

Final set: 12 properties after consolidation.

---

### Property 1: AppShell renders shell on all defined routes

*For any* path in the set of 5 defined routes (`/`, `/forecast`, `/ask`, `/data-entry`, `/recommendations`), rendering the application at that path SHALL include both the Sidebar and TopBar elements in the DOM.

**Validates: Requirements 4.1**

---

### Property 2: Active nav item tracks current route

*For any* of the 5 defined route paths, the navigation item whose `to` path matches the current route SHALL have the active CSS class applied, and no other navigation item SHALL have the active class.

**Validates: Requirements 5.3**

---

### Property 3: Theme toggle round-trip persists to localStorage

*For any* initial theme value stored in `localStorage` under `wattif-theme`, loading the application SHALL apply that stored theme to `document.documentElement.dataset.theme`; toggling the theme SHALL update both `dataset.theme` and the stored value; toggling again SHALL restore the original state.

**Validates: Requirements 6.3, 6.4, 6.6**

---

### Property 4: StatCard renders semantic dl/dt/dd structure with correct fonts

*For any* `label`, `value`, and optional `unit` string, rendering a `StatCard` SHALL produce a `<dl>` element containing exactly one `<dt>` (with the label text and `--font-sans`) and one `<dd>` (with the value text and `--font-mono`).

**Validates: Requirements 7.6, 18.6**

---

### Property 5: Anomaly card appears if and only if first-month forecast exceeds 110% of mean

*For any* array of `ForecastMonth` objects with at least 2 entries, the `detectAnomaly` function SHALL return a non-null result if and only if `months[0].kwh_forecast > 1.1 × mean(months.map(m => m.kwh_forecast))`. When non-null, the returned `percentAbove` SHALL equal `((months[0].kwh_forecast − mean) / mean) × 100` rounded to one decimal place.

**Validates: Requirements 7.3**

---

### Property 6: Dashboard always renders exactly 4 StatCards when forecast data is available

*For any* non-empty `ForecastResponse`, rendering `DashboardPage` with that data SHALL produce exactly 4 `StatCard` elements in the DOM.

**Validates: Requirements 7.1**

---

### Property 7: HorizonSelector active button uses accent tokens for any selected horizon

*For any* horizon value in `{1, 3, 6}`, rendering `HorizonSelector` with that horizon as `selected` SHALL apply `--color-accent-primary` background and `--color-text-on-accent` text to exactly the button corresponding to the selected horizon, and apply `--color-input-fill` background to all other buttons.

**Validates: Requirements 8.7**

---

### Property 8: ChatPanel message bubbles use correct token-based colours for any message role

*For any* message with role `user`, `assistant`, or `error`, rendering the message bubble in `ChatPanel` SHALL apply:
- `user`: background `var(--color-accent-primary)`, colour `var(--color-text-on-accent)`
- `assistant`: background `var(--color-card-bg)`, border `1px solid var(--color-border)`, colour `var(--color-text-primary)`
- `error`: a background derived from `--color-red`, colour `var(--color-red)`

**Validates: Requirements 9.2, 9.3, 9.4**

---

### Property 9: Valid DataEntry form submission grows SessionLog by exactly 1

*For any* valid triple of (date string, time string, kwh number ≥ 0) submitted via the New Reading form, the `sessionLog` length SHALL increase by exactly 1, all four form fields SHALL be reset to empty, and the new row SHALL have `source: 'Manual'`.

**Validates: Requirements 10.2**

---

### Property 10: Invalid DataEntry form submission leaves SessionLog unchanged

*For any* non-empty subset of {date, time, kwh} left blank in the New Reading form submission, the `sessionLog` length SHALL remain unchanged and validation error messages SHALL be present in the DOM for each blank required field.

**Validates: Requirements 10.3**

---

### Property 11: SessionLog date/time/kwh cells use --font-mono

*For any* `SessionLogEntry`, the rendered `<td>` cells for Date, Time, and kWh SHALL reference `var(--font-mono)` in their computed font-family.

**Validates: Requirements 10.7**

---

### Property 12: ModelEvaluation numeric values use --font-mono for any valid ModelInfoResponse

*For any* `ModelInfoResponse` with non-null `mape_kwh_pct`, `mape_price_pct`, or `mape_avg_pct` values, the rendered numeric text for those values SHALL reference `var(--font-mono)` in their computed font-family.

**Validates: Requirements 16.1**


---

## Testing Strategy

### Dual Testing Approach

Unit tests cover specific examples, edge cases, error conditions, and structural checks (routing, component rendering, ARIA presence). Property tests cover universal invariants across generated inputs.

### Property-Based Tests (fast-check)

Each test runs **≥ 100 iterations**. Tag format: `// Feature: ui-redesign, Property N: <property_text>`

| Property | Test file | fast-check arbitraries used |
|---|---|---|
| 1 — AppShell on all routes | `AppShell.test.tsx` | `fc.constantFrom(...routes)` |
| 2 — Active nav item | `Sidebar.test.tsx` | `fc.constantFrom(...routes)` |
| 3 — Theme round-trip | `ThemeContext.test.tsx` | `fc.constantFrom('light', 'dark')` |
| 4 — StatCard dl/dt/dd | `StatCard.test.tsx` | `fc.string()`, `fc.string()`, `fc.option(fc.string())` |
| 5 — Anomaly detection | `DashboardPage.test.tsx` | `fc.array(fc.record({ kwh_forecast: fc.float(...) }), { minLength: 2 })` |
| 6 — 4 StatCards | `DashboardPage.test.tsx` | `fc.array(forecastMonthArb, { minLength: 1 })` |
| 7 — HorizonSelector tokens | `HorizonSelector.test.tsx` | `fc.constantFrom(1, 3, 6)` |
| 8 — ChatPanel bubble tokens | `ChatPanel.test.tsx` | `fc.constantFrom('user', 'assistant', 'error')` with `fc.string()` |
| 9 — Valid form grows log | `DataEntryPage.test.tsx` | `fc.record({ date: dateArb, time: timeArb, kwh: fc.float({ min: 0, max: 999999 }) })` |
| 10 — Invalid form no change | `DataEntryPage.test.tsx` | `fc.subarray(['date', 'time', 'kwh'], { minLength: 1 })` |
| 11 — SessionLog font-mono | `DataEntryPage.test.tsx` | `fc.array(sessionLogEntryArb, { minLength: 1 })` |
| 12 — ModelEvaluation font-mono | `ModelEvaluation.test.tsx` | `fc.record({ mape_kwh_pct: fc.float(...), ... })` |

### Unit / Example-Based Tests

- Route rendering: one test per route verifies correct page component renders.
- 404 redirect: 3 example invalid paths verify redirect to `/`.
- Dark mode: toggle applies `data-theme="dark"` to `<html>`.
- OfflineBanner: shows when `navigator.onLine = false`, hides when online.
- ModelStatusPill: shows "MODEL ACTIVE" with mocked valid response, "MODEL NOT TRAINED" with null mape.
- HealthIndicator: connecting / operational / degraded / unreachable states.
- ForecastPage 503 error → alert message rendered.
- ForecastPage auto-loads on mount (mock `getForecast` called with horizon 3).
- SessionLog empty state message rendered when log is empty.
- UploadPanel `onUploadSuccess` appends CSV row to SessionLog.
- Recommendations page card renders correct text.
- AnomalyCard renders with teal left border style.

### Test Environment Notes

- `@testing-library/react` with `happy-dom` (existing vitest config).
- CSS variables cannot be resolved in jsdom/happy-dom; token assertions verify the CSS `var()` reference string (e.g., `expect(el).toHaveStyle('font-family: var(--font-mono)')`) rather than resolved computed values.
- Router context is provided via `MemoryRouter` in tests for components that use `useLocation` / `NavLink`.


---

## Implementation Notes / Migration Path

### Dependency Changes

```bash
# Add react-router-dom as a production dependency
npm install react-router-dom@^6.28.0
```

No other new production dependencies are required. `fast-check` is already a dev dependency.

### Vite Config Changes

No changes to `vite.config.ts` are required. The dev server already serves `index.html` for all paths. The PWA workbox config is unaffected — the new routes are client-side and all served from `index.html`.

### `index.html` Changes

1. Add Google Fonts preconnect + stylesheet link elements (before `</head>`).
2. Viewport meta tag is already present (`width=device-width, initial-scale=1.0`) — no change needed.
3. `<meta name="theme-color">` is already `#1a1a2e` (matches `--color-sidebar-bg`) — no change.

### `main.tsx` Changes

```tsx
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { ForecastProvider } from './context/ForecastContext'
import './styles/tokens.css'   // ← import order: tokens first
import './styles/index.css'    // ← then global styles

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <ForecastProvider>
          <App />
        </ForecastProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
)
```

### `App.tsx` Changes

The monolithic `App.tsx` is reduced to a route table. All state management moves to `ForecastContext`.

### Component Migration Checklist

Each modified component follows the same migration pattern:
1. Remove all hardcoded hex colour literals.
2. Replace with `var(--token-name)` references in inline `style` props.
3. Replace hardcoded button styles with `.btn-primary` / `.btn-secondary` class names.
4. Replace hardcoded card styles with `.card` class or equivalent `var()` inline styles.
5. Run existing tests — update any snapshot or style assertions.

### tsconfig / TypeScript

No `tsconfig.json` changes are required. `react-router-dom` v6 ships its own types.

### Icon Strategy

Navigation icons are sourced from inline SVG snippets (no icon library added). The 5 required icons (dashboard grid, chart, chat bubble, database/upload, lightbulb/recommendations) plus settings gear can be extracted from public domain SVG sources or drawn minimally. This avoids adding a dependency like `lucide-react` or `heroicons` for a small icon set. If the team prefers a library, `lucide-react` (MIT, tree-shakeable) is the recommended choice.

### Existing Tests

The existing 4 test files (`ChatPanel.test.tsx`, `ForecastChart.test.tsx`, `HorizonSelector.test.tsx`, `UploadPanel.test.tsx`) will require updates wherever they:
- Assert specific hardcoded hex colour values → update to assert `var(--token)` strings.
- Import from paths that change (e.g. if files move).
- Reference the `App` component for integration tests → wrap with `MemoryRouter` + providers.

All other test logic (behaviour assertions) remains valid.
