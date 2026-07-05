# Implementation Plan: UI Redesign

## Overview

Transform the WATT-IF frontend from a single-page, vertically-stacked layout with inline styles into a multi-page, sidebar-navigated application using a formal CSS design token system, `react-router-dom` v6 routing, and five distinct route pages. All existing backend integrations remain functionally unchanged.

## Tasks

- [x] 1. Install dependency and create CSS foundations
  - Run `npm install react-router-dom@^6.28.0` inside `frontend/`
  - Create `frontend/src/styles/tokens.css` with all `:root` CSS custom properties and `[data-theme="dark"]` override block as specified in the design (colour, typography, spacing, shadow, and rating-level tokens)
  - Create `frontend/src/styles/index.css` with global body reset, `.card`, `.btn-primary`, `.btn-secondary`, responsive StatCard grid (`.stat-grid`), app-shell layout classes (`.app-shell`, `.app-shell__sidebar`, `.app-shell__main`, `.app-shell__overlay`), and mobile breakpoint rules
  - Update `frontend/index.html` to add Google Fonts preconnect and stylesheet `<link>` elements for Inter (400, 500, 600, 700) and Space Mono (400, 700) with `display=swap`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 13.1, 13.2, 13.3, 13.4, 13.5, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6_

- [x] 2. Create ThemeContext and ForecastContext
  - [x] 2.1 Create `frontend/src/context/ThemeContext.tsx`
    - Implement `ThemeProvider` with `theme` state, initialised synchronously from `localStorage.getItem('wattif-theme')` (defaults to `'light'`)
    - Apply `document.documentElement.dataset.theme` on every state change
    - Persist to `localStorage` under key `wattif-theme` on every toggle
    - Export `useTheme` hook
    - _Requirements: 6.3, 6.4, 6.6_

  - [ ]* 2.2 Write property test for ThemeContext round-trip
    - **Property 3: Theme toggle round-trip persists to localStorage**
    - **Validates: Requirements 6.3, 6.4, 6.6**
    - Use `fc.constantFrom('light', 'dark')` as the initial theme arbitrary

  - [x] 2.3 Create `frontend/src/context/ForecastContext.tsx`
    - Lift `months`, `horizon`, `loading`, `error`, `loadForecast`, `setHorizon`, `setMonths` state out of App into `ForecastProvider`
    - On mount, mirror the existing App.tsx logic: check training status, auto-load 3-month forecast if not running
    - Handle 503 vs other errors identically to existing App.tsx
    - Export `useForecast` hook
    - _Requirements: 8.2, 8.4, 8.5, 8.6_

- [x] 3. Update entry point and route table
  - [x] 3.1 Update `frontend/src/main.tsx`
    - Wrap the app in `<BrowserRouter>`, `<ThemeProvider>`, `<ForecastProvider>` in that order
    - Import `./styles/tokens.css` before `./styles/index.css` (tokens first, then global styles)
    - _Requirements: 1.5, 3.1, 3.2_

  - [x] 3.2 Replace `frontend/src/App.tsx` with route table
    - Reduce App.tsx to a `<Routes>` table with `<Route path="/" element={<AppShell />}>` as the parent
    - Add nested routes: index → `DashboardPage`, `/forecast` → `ForecastPage`, `/ask` → `AskPage`, `/data-entry` → `DataEntryPage`, `/recommendations` → `RecommendationsPage`
    - Add `<Route path="*" element={<Navigate replace to="/" />} />` for unknown routes
    - _Requirements: 3.3, 3.4, 3.5, 3.6_

- [x] 4. Build AppShell component
  - [x] 4.1 Create `frontend/src/components/AppShell.tsx`
    - Render `<OfflineBanner>` above the shell grid with `position: sticky; top: 0; z-index: 1000`
    - Render a two-column CSS grid (`220px 1fr`) on desktop collapsing to `1fr` on mobile via the `.app-shell` class
    - Manage `sidebarOpen` local state; pass `open`, `onClose` to `<Sidebar>` and `onMenuClick` to `<TopBar>`
    - Render overlay `<div class="app-shell__overlay">` that closes the drawer on click
    - Attach a `keydown` listener on `document` (via `useEffect`) to close drawer on `Escape`
    - Implement focus-trap: on open, save `document.activeElement` as `returnFocusRef`, focus first nav item in drawer, intercept `Tab`/`Shift+Tab` within drawer; on close, return focus to `returnFocusRef.current`
    - Use `<Outlet>` for the page content area
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 18.2, 18.3, 18.5_

  - [ ]* 4.2 Write property test for AppShell shell presence on all routes
    - **Property 1: AppShell renders shell on all defined routes**
    - **Validates: Requirements 4.1**
    - Use `fc.constantFrom('/', '/forecast', '/ask', '/data-entry', '/recommendations')` with `MemoryRouter`

- [x] 5. Build Sidebar and TopBar components
  - [x] 5.1 Create `frontend/src/components/Sidebar.tsx`
    - Render WATT-IF logo (`wattif.png`) and "ENERGY INTELLIGENCE" subtitle at the top
    - Render 5 `<NavLink>` items (Dashboard, Forecast, Ask WATT-IF, Recommendations, Data Entry) with `className` callback applying `.nav-item--active` when `isActive`, using `end` prop for the root path
    - Include inline SVG icons for each nav item and the Settings link
    - Render `<HealthIndicator>` below the nav list
    - Render `<ModelStatusPill>` above the Settings link
    - Render Settings `<a href="#">` at the very bottom
    - Apply `--color-sidebar-bg` background and `--shadow-sidebar` box-shadow
    - Add `aria-label="Main navigation"` on the `<nav>` element
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.8, 14.1, 18.1_

  - [ ]* 5.2 Write property test for active nav item tracking current route
    - **Property 2: Active nav item tracks current route**
    - **Validates: Requirements 5.3**
    - Use `fc.constantFrom('/', '/forecast', '/ask', '/data-entry', '/recommendations')` with `MemoryRouter initialEntries`

  - [x] 5.3 Create `frontend/src/components/TopBar.tsx`
    - Read current route via `useLocation()` and map to page title string per the design table
    - Render page title as `<h1>`
    - Render hamburger `<button aria-label="Open navigation menu">` visible only on mobile (`max-width: 767px`)
    - Render `DarkModeToggle`, notifications `<button aria-label="Notifications">`, and avatar `<button aria-label="User account">` on the right
    - Notifications and avatar buttons have no functional action
    - _Requirements: 6.1, 6.2, 6.5, 4.4, 18.4_

  - [x] 5.4 Create `frontend/src/components/ModelStatusPill.tsx`
    - Poll `/model-info` on mount and every 60 seconds via `setInterval`; clean up on unmount
    - If `mape_avg_pct` is non-null: display green pill "MODEL ACTIVE · MAPE X.X%"
    - If loading, null, or error: display "MODEL NOT TRAINED" using `--color-text-muted`
    - Use `--font-mono` for the MAPE value
    - _Requirements: 5.5, 5.6, 5.7_

  - [x] 5.5 Create `frontend/src/components/DarkModeToggle.tsx`
    - Render an icon `<button>` with `aria-label="Toggle dark mode"` that calls `toggleTheme()` from `useTheme()`
    - Display sun icon when dark theme is active, moon icon when light theme is active
    - _Requirements: 6.2, 6.3, 18.4_

- [x] 6. Checkpoint — Ensure routing and shell pass all tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Build new page components
  - [x] 7.1 Create `frontend/src/components/StatCard.tsx`
    - Render a `<dl>` with one `<dt>` (label, `--font-sans`, `--color-text-muted`) and one `<dd>` (value + optional unit, `--font-mono`, `--color-text-primary`)
    - Apply `.card` class for container styling
    - Accept `label: string`, `value: string | number`, `unit?: string` props
    - _Requirements: 7.6, 18.6_

  - [ ]* 7.2 Write property test for StatCard semantic structure and fonts
    - **Property 4: StatCard renders semantic dl/dt/dd structure with correct fonts**
    - **Validates: Requirements 7.6, 18.6**
    - Use `fc.string()`, `fc.string()`, `fc.option(fc.string())` for label, value, unit

  - [x] 7.3 Create `frontend/src/components/AnomalyCard.tsx`
    - Accept `month: string` and `percentAbove: number` props
    - Render card with 4 px left border using `--color-teal`
    - Display "Anomaly Detected: forecast consumption for [month] is [X.X]% above your average."
    - Apply standard `.card` class tokens
    - _Requirements: 7.3, 7.7_

  - [x] 7.4 Create `frontend/src/pages/DashboardPage.tsx`
    - Read `months`, `loading`, `error` from `useForecast()`
    - If `loading`: render loading skeleton (4 placeholder stat cards + chart placeholder)
    - If `months.length === 0` and not loading and no error: render empty-state prompt card directing user to Data Entry
    - Otherwise: render `.stat-grid` with 4 `StatCard` components ("This Month kWh", "Daily Average kWh/day", "Temp Today °C" = "—", "Humidity %" = "—")
    - Implement `detectAnomaly(months)` pure function per the design spec and conditionally render `<AnomalyCard>`
    - Render `<ForecastChart months={months} />` in a "Consumption History" section
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 7.5 Write property test for anomaly detection logic
    - **Property 5: Anomaly card appears if and only if first-month forecast exceeds 110% of mean**
    - **Validates: Requirements 7.3**
    - Use `fc.array(fc.record({ kwh_forecast: fc.float({ min: 0, max: 9999, noNaN: true }) }), { minLength: 2 })` for month arrays

  - [ ]* 7.6 Write property test for DashboardPage always renders 4 StatCards
    - **Property 6: Dashboard always renders exactly 4 StatCards when forecast data is available**
    - **Validates: Requirements 7.1**
    - Use `fc.array(forecastMonthArb, { minLength: 1 })` with mocked `useForecast`

  - [x] 7.7 Create `frontend/src/pages/ForecastPage.tsx`
    - Read and write `months`, `horizon`, `loading`, `error`, `loadForecast`, `setHorizon` from `useForecast()`
    - On mount, if `months.length === 0`, call `loadForecast(3)`
    - Render `<HorizonSelector>` (disabled while loading) and `<ForecastChart>`
    - While loading: render `<span role="status">Loading…</span>`
    - On 503 error: render "No trained model found — upload a CSV on the Data Entry page to train the model first." in `<p role="alert">`
    - On other error: render human-readable message in `<p role="alert">`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 7.8 Create `frontend/src/pages/AskPage.tsx`
    - Render `<ChatPanel>` in a wrapper that fills 100% of viewport height below the TopBar
    - _Requirements: 9.1_

  - [x] 7.9 Create `frontend/src/pages/DataEntryPage.tsx`
    - Implement New Reading form with Date (required), Time (required), kWh number (required, min 0, max 999999), and Label (optional, maxLength 100) fields, plus Submit button
    - On valid submit: append row to `sessionLog` with `source: 'Manual'`, reset all fields
    - On invalid submit: display inline per-field validation messages for each empty required field; do not append to log
    - Render `<UploadPanel>` with `onUploadSuccess` callback that appends a CSV Upload row with current timestamp, `kwh: "—"`, label = filename
    - Render SessionLog table with columns (Date, Time, kWh, Label, Source); Date/Time/kWh cells use `--font-mono`
    - Empty state: render "No entries recorded yet this session." when `sessionLog.length === 0`
    - Form input fields use `--color-input-fill` background, `--color-border` border, `--font-sans` font
    - Submit button uses `.btn-primary` class
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9_

  - [ ]* 7.10 Write property test for valid DataEntry form submission grows SessionLog by exactly 1
    - **Property 9: Valid DataEntry form submission grows SessionLog by exactly 1**
    - **Validates: Requirements 10.2**
    - Use `fc.record({ date: fc.string(), time: fc.string(), kwh: fc.float({ min: 0, max: 999999, noNaN: true }) })`

  - [ ]* 7.11 Write property test for invalid DataEntry form submission leaves SessionLog unchanged
    - **Property 10: Invalid DataEntry form submission leaves SessionLog unchanged**
    - **Validates: Requirements 10.3**
    - Use `fc.subarray(['date', 'time', 'kwh'], { minLength: 1 })` to determine which required fields are left blank

  - [ ]* 7.12 Write property test for SessionLog date/time/kwh cells use --font-mono
    - **Property 11: SessionLog date/time/kwh cells use --font-mono**
    - **Validates: Requirements 10.7**
    - Use `fc.array(sessionLogEntryArb, { minLength: 1 })` to pre-populate the session log

  - [x] 7.13 Create `frontend/src/pages/RecommendationsPage.tsx`
    - Render a single `.card` with heading "Recommendations" and body text "Personalised energy-saving recommendations will appear here once the feature is available."
    - Apply `--color-card-bg` background, `1px solid var(--color-border)` border, `--radius-card` border-radius, `--shadow-card` box-shadow
    - _Requirements: 11.1, 11.2, 11.3_

- [x] 8. Checkpoint — Ensure all page components and PBT tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Restyle existing components to use design tokens
  - [x] 9.1 Modify `frontend/src/components/ChatPanel.tsx`
    - Replace all hardcoded hex values with CSS variable references per the design migration table (user bubble → `--color-accent-primary`/`--color-text-on-accent`; assistant bubble → `--color-card-bg`/`--color-border`/`--color-text-primary`; error bubble → `--color-red`; thread bg → `--color-input-fill`; submit button → `--color-accent-primary` / `--color-text-muted` disabled; input border → `--color-border`, input bg → `--color-input-fill`)
    - Apply `.btn-primary` class to the submit button
    - Apply `.card` class (or equivalent token inline styles) to the outer `<section>`
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 12.1_

  - [ ]* 9.2 Write property test for ChatPanel message bubble token colours
    - **Property 8: ChatPanel message bubbles use correct token-based colours for any message role**
    - **Validates: Requirements 9.2, 9.3, 9.4**
    - Use `fc.constantFrom('user', 'assistant', 'error')` combined with `fc.string()` for message text

  - [x] 9.3 Modify `frontend/src/components/ForecastChart.tsx`
    - Replace the `colors` constants object with CSS variable references (`var(--color-accent-primary)`, `var(--color-red)`, `var(--color-border)`, `var(--color-text-primary)`, `var(--color-text-muted)`, `var(--color-card-bg)`, `var(--color-page-bg)`)
    - Migrate `chartCardStyle` to use token inline styles for background, border, borderRadius, boxShadow
    - Retain all Recharts chart structure and data processing unchanged
    - _Requirements: 12.1_

  - [x] 9.4 Modify `frontend/src/components/HorizonSelector.tsx`
    - Active button: `background: var(--color-accent-primary)`, `color: var(--color-text-on-accent)`, `border: 2px solid var(--color-accent-primary)`, `border-radius: var(--radius-card)`
    - Inactive button: `background: var(--color-input-fill)`, `color: var(--color-text-primary)`, `border: 2px solid var(--color-border)`, `border-radius: var(--radius-card)`
    - Disabled state: `cursor: not-allowed`
    - _Requirements: 8.7, 13.1_

  - [ ]* 9.5 Write property test for HorizonSelector active button tokens
    - **Property 7: HorizonSelector active button uses accent tokens for any selected horizon**
    - **Validates: Requirements 8.7**
    - Use `fc.constantFrom(1, 3, 6)` for the selected horizon

  - [x] 9.6 Modify `frontend/src/components/HealthIndicator.tsx`
    - Replace all hardcoded hex values with design tokens (`--color-teal`, `--color-amber`, `--color-red`, `--color-text-muted`)
    - Connecting state → `--color-text-muted` with "Connecting…" text
    - Unreachable state → "Backend offline" text using `--color-red`
    - All-operational state → single dot + "All systems operational" in `--color-teal`
    - Degraded state → one dot per subsystem; degraded dots use `--color-amber`, operational dots use `--color-teal`
    - Remove the `last_upload_at` / `model_trained_at` timestamp display lines (that info is surfaced elsewhere)
    - The component is now rendered inside `Sidebar` — confirm it has no wrapper styles that assume header placement
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [x] 9.7 Modify `frontend/src/components/OfflineBanner.tsx`
    - Replace `background: '#ff9800'` with `background: var(--color-accent-primary)`, `color: var(--color-sidebar-bg)`
    - Add `position: sticky; top: 0; z-index: 1000` so it overlays the shell without displacing it
    - _Requirements: 15.1, 15.2, 15.3_

  - [x] 9.8 Modify `frontend/src/components/UploadPanel.tsx`
    - Replace inline upload button styles with `.btn-primary` CSS class
    - Apply `.card` class (or token inline styles) to the outer `<section>`
    - _Requirements: 12.1, 13.6_

  - [x] 9.9 Modify `frontend/src/components/ModelEvaluation.tsx`
    - Replace all `RATING_COLOR`/`RATING_BG` maps with CSS class references `.rating-badge--excellent`, `.rating-badge--good`, `.rating-badge--fair`, `.rating-badge--poor` that use `--color-rating-*` tokens defined in `tokens.css`
    - Wrap all numeric metric values (MAPE percentages, ARIMA order tuples) in `<span style={{ fontFamily: 'var(--font-mono)' }}>`
    - Replace all `background`, `border`, and text colour inline styles with token references (`--color-card-bg`, `--color-border`, `--color-text-primary`, `--color-text-muted`, `--color-page-bg`)
    - _Requirements: 16.1, 16.2, 16.3_

  - [ ]* 9.10 Write property test for ModelEvaluation numeric values use --font-mono
    - **Property 12: ModelEvaluation numeric values use --font-mono for any valid ModelInfoResponse**
    - **Validates: Requirements 16.1**
    - Use `fc.record({ mape_kwh_pct: fc.float({ min: 0, max: 100, noNaN: true }), mape_price_pct: fc.float({ min: 0, max: 100, noNaN: true }), mape_avg_pct: fc.float({ min: 0, max: 100, noNaN: true }) })`

- [x] 10. Checkpoint — Ensure all component restyling tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Update existing test files and add new unit tests
  - [x] 11.1 Update `frontend/src/test/ChatPanel.test.tsx`
    - Replace any hardcoded hex colour assertions with `var(--token)` string assertions
    - Wrap render calls with `MemoryRouter` + context providers if needed
    - _Requirements: 9.2, 9.3, 9.4_

  - [x] 11.2 Update `frontend/src/test/ForecastChart.test.tsx`
    - Replace any hardcoded hex colour assertions with `var(--token)` string assertions
    - _Requirements: 12.1_

  - [x] 11.3 Update `frontend/src/test/HorizonSelector.test.tsx`
    - Replace hardcoded colour assertions with token string assertions
    - Wrap render calls with providers if needed
    - _Requirements: 8.7_

  - [x] 11.4 Update `frontend/src/test/UploadPanel.test.tsx`
    - Update any style assertions to match token-based styling
    - Wrap render calls with providers if needed
    - _Requirements: 12.1, 13.6_

  - [x] 11.5 Create `frontend/src/test/AppShell.test.tsx`
    - Unit tests: each of the 5 routes renders the correct page component; 404 path redirects to `/`; OfflineBanner renders above shell; hamburger button visible on mobile viewport
    - _Requirements: 3.3, 3.4, 4.1, 4.2, 4.4_

  - [x] 11.6 Create `frontend/src/test/StatCard.test.tsx`
    - Unit tests: renders `<dl>`, `<dt>`, `<dd>`; optional unit appended; correct `var(--font-mono)` on value and `var(--font-sans)` on label
    - _Requirements: 7.6, 18.6_

  - [x] 11.7 Create `frontend/src/test/DashboardPage.test.tsx`
    - Unit tests: loading skeleton renders; empty-state prompt renders; AnomalyCard renders when anomaly detected; AnomalyCard absent when no anomaly; 4 StatCards rendered when data present
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 11.8 Create `frontend/src/test/ForecastPage.test.tsx`
    - Unit tests: auto-loads on mount (mock `getForecast` called with horizon 3); 503 error renders correct alert message; network error renders human-readable message; loading indicator has `role="status"`
    - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 11.9 Create `frontend/src/test/DataEntryPage.test.tsx`
    - Unit tests: empty SessionLog state renders correct message; UploadPanel `onUploadSuccess` appends CSV row; per-field validation shows messages without appending row
    - _Requirements: 10.3, 10.6, 10.9_

  - [x] 11.10 Create `frontend/src/test/ThemeContext.test.tsx`
    - Unit tests: dark mode toggle applies `data-theme="dark"` to `<html>`; second toggle restores light theme; persists correct key to localStorage; reads stored preference on load
    - _Requirements: 6.3, 6.4, 6.6_

- [x] 12. Final checkpoint — Ensure all tests pass
  - Run `npm test` in `frontend/` and ensure all tests pass.
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The design already uses TypeScript/React throughout — no language selection step needed
- react-router-dom v6 is the only new production dependency; fast-check is already installed
- CSS variable assertions in tests check the `var(--token)` reference string, not the resolved computed value, because happy-dom cannot resolve CSS custom properties
- Property tests are tagged `// Feature: ui-redesign, Property N: <property_text>` as per the testing strategy
- All new page components in `src/pages/` use `useForecast()` or `useTheme()` hooks — wrap test renders with the appropriate providers via `MemoryRouter` + context wrappers
- The HealthIndicator is moved from the header to the Sidebar; the existing component file is modified in-place (task 9.6), not relocated

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1", "2.3"] },
    { "id": 1, "tasks": ["2.2", "3.1", "3.2"] },
    { "id": 2, "tasks": ["4.1", "5.4", "5.5", "7.1", "7.3"] },
    { "id": 3, "tasks": ["4.2", "5.1", "5.3", "7.2", "7.4", "7.13"] },
    { "id": 4, "tasks": ["5.2", "7.5", "7.6", "7.7", "7.8", "7.9"] },
    { "id": 5, "tasks": ["7.10", "7.11", "7.12", "9.1", "9.3", "9.4", "9.6", "9.7", "9.8", "9.9"] },
    { "id": 6, "tasks": ["9.2", "9.5", "9.10", "11.1", "11.2", "11.3", "11.4", "11.5", "11.6", "11.7", "11.8", "11.9", "11.10"] }
  ]
}
```
