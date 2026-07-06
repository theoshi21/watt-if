# WATT-IF Test Plan

**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

## 1. Introduction

WATT-IF is a locally-hosted Progressive Web App (PWA) that helps Philippine households forecast their monthly electricity consumption and bills. It connects to a FastAPI backend running on the user's own machine, using a SARIMAX model for forecasting, a RAG-powered chat assistant (via Ollama), and live Meralco rate data for bill calculations.

This test plan defines the scope, approach, and schedule for manual functional testing of the WATT-IF web application. Its purpose is to verify that all user-facing features work correctly, handle bad inputs gracefully, and provide a reliable experience across normal and edge-case conditions.

**Scope:** Manual black-box functional testing of the WATT-IF web application — covering data entry, forecasting, the chat assistant, the price calculator, the dashboard, and general UI/UX behaviors. Backend internals, ML model accuracy, and automated performance benchmarks are explicitly out of scope.

**Intended audience:** Project stakeholders, developers, and testers involved in the WATT-IF project.

---

## 2. Test Items

The following screens, forms, buttons, and components are in scope for testing:

- **New Reading form** (Data Entry page) — month picker, kWh input, optional bill/rate overrides, live bill preview, submit button
- **CSV Upload** (Data Entry page) — file selector, upload button, upload result message
- **Train Model button** (Data Entry page) — trigger, status display, model info panel after completion
- **Entry History table** (Data Entry page) — paginated list of all entries, inline edit/delete per row
- **Clear All Data button** (Data Entry page) — confirmation panel and destructive action
- **Forecast page** — horizon selector (1/3/6/9/12m), kWh bar chart, bill line chart, confidence interval display
- **Ask WATT-IF chat** — message input, Ask button, streaming response display, Clear Chat button
- **Price Calculator** — kWh input, customer type selector, bracket selector, bill breakdown table, rate refresh button
- **Dashboard** — stat cards (This Month, Daily Average, Avg Temp, Avg Humidity), anomaly card, forecast chart, loading skeleton, empty state
- **Dark/light mode toggle** — theme switch, persistence across page refreshes
- **Navigation sidebar** — links to all five pages, active state highlighting, mobile hamburger menu
- **Health indicator** — status dots for all subsystems (backend, model, Ollama, data)

---

## 3. Features to Be Tested

### Data Entry
- New Reading form: valid input acceptance, field validation (blank, zero, negative, non-numeric kWh), live bill preview as you type, duplicate month handling, optional field behavior
- CSV Upload: valid CSV with minimum columns, valid CSV with all extended columns, invalid file types, missing required columns, blank values (imputation), duplicate months, re-upload behavior
- Train Model: trigger with sufficient data, trigger with no data, status transitions (Idle → Training → Done/Failed), model info update after training, concurrent training prevention
- Entry History (Edit): inline edit row activation, valid/invalid kWh edits, saving null bill amount, cancel edit, multi-row edit conflict
- Entry History (Delete): confirmation dialog, confirmed delete, cancelled delete, delete last entry
- Pagination: row count per page, page navigation, first/last page buttons, entry count label, hidden pagination for small datasets
- Clear All Data: confirmation panel, confirmed clear, cancelled clear, effect on model (forecast should return 503 after clearing), re-upload after clearing

### Forecast
- Horizon selection: all five options (1, 3, 6, 9, 12 months), chart update on selection
- Chart display: kWh bar chart with error bars, bill line chart with shaded CI band, tooltip on hover
- Data anchoring: forecast months start from the month after the latest data entry
- Error/empty states: no trained model, no data at all

### Chat (Ask WATT-IF)
- Sending messages: question submission via button and keyboard, empty message prevention
- Response display: streaming text display, completion
- Input limits: long question acceptance (500 chars), character limit enforcement
- Scope handling: out-of-scope questions declined politely
- History: persistence after page navigation, loading on page mount
- Clear Chat: clears UI and database, persists after navigating away
- Offline: graceful error when Ollama is unavailable

### Price Calculator
- Input handling: valid kWh, zero, negative, boundary values, very large values
- Rate loading: live Meralco rate shown on page load, fallback behavior when API is unavailable
- Bracket logic: auto-selection for given kWh, manual override, update on customer type change
- Bill breakdown: correct calculation and display of all charge components
- Rate refresh: manual refresh updates rate and recalculates bill

### Dashboard
- Stat cards: correct values (This Month kWh, Daily Average, Avg Temp, Avg Humidity)
- Anomaly detection: anomaly card shown when first forecast month > 110% of mean, absent otherwise
- Forecast chart: renders correctly
- Loading state: skeleton shown while data is loading
- Empty state: appropriate message when no forecast is available

### UI/UX
- Dark/light mode: toggle switches theme, preference persists after reload
- Sidebar navigation: each link navigates to the correct page, active item highlighted
- Mobile responsiveness: hamburger menu opens/closes sidebar, overlay tap and Escape key close sidebar
- Health indicator: all-green when all systems up, degraded when Ollama is offline
- Offline banner: appears when network connection is lost

---

## 4. Features Not to Be Tested

The following are explicitly out of scope for this test plan:

- **Internal ML model accuracy** — statistical validation of SARIMAX forecast quality (e.g., MAPE benchmarks, residual analysis) is the responsibility of the data science team, not the QA process
- **Automated background training performance** — training speed or memory benchmarks are not tested manually
- **Ollama LLM response quality** — whether the language model gives factually correct or well-reasoned answers is not evaluated here; only that responses are delivered without errors
- **Third-party API reliability** — the Meralco rate scraper, Open-Meteo, and NOAA ENSO services are external dependencies; their uptime and data accuracy are not tested
- **Cross-browser compatibility beyond Chrome and Safari** — testing is limited to the two primary supported browsers
- **Security penetration testing** — no authentication bypass, injection, or security-specific tests are included in this plan

---

## 5. Approach

Testing follows a **black-box** approach: testers interact with the application exactly as an end user would, without any knowledge of the underlying source code or database structure. No code inspection is required to execute any test case.

All testing is **manual and exploratory**. Testers follow the step-by-step instructions in each test case and record the actual result against the expected result.

Three testing techniques are applied across all test items:

1. **Valid input testing** — confirm the system accepts correct inputs and produces the expected output
2. **Invalid input testing** — confirm the system rejects or handles incorrect inputs gracefully (error messages, no crashes)
3. **Boundary value analysis** — test values at the edges of accepted ranges (e.g., minimum kWh, maximum kWh, exactly at and just beyond the limit)

For UI/UX and navigation tests, a combination of visual inspection and interaction testing is used.

---

## 6. Item Pass/Fail Criteria

| Area | Pass | Fail |
|---|---|---|
| **Forms** | Valid inputs are accepted and saved; invalid inputs show a clear error message; no data is saved for invalid inputs | Form accepts invalid input without error, or rejects valid input, or crashes |
| **Charts** | Data renders without visual errors; values and labels match the expected forecast data | Chart is blank, throws an error, or displays incorrect values |
| **CRUD operations** | Create, read, update, and delete actions all reflect correctly in the UI immediately after the action | Any operation silently fails, shows stale data, or causes an unhandled error |
| **Chat** | Messages are sent successfully; responses stream and complete without errors; history loads correctly | Message fails to send, response is never delivered, or page crashes |
| **Price Calculator** | Bill total and per-component breakdown match the expected calculation for the given kWh and rate | Any component shows an incorrect value or the total doesn't match the sum of components |
| **General (all areas)** | — | Any unhandled JavaScript exception, blank white screen, or application crash constitutes an automatic fail |

---

## 7. Test Deliverables

The following documents and outputs will be produced as part of this test effort:

1. **Test Plan** *(this document)* — defines scope, approach, criteria, and schedule
2. **Test Cases** (`Test_Cases.md`) — complete set of manual test cases with steps, expected results, and result columns for testers to fill in
3. **Test Data Sets** — `data/synthetic_2022_2025.csv` (48-month synthetic Philippine dataset) plus the specific manual entry values defined within individual test cases
4. **Test Scripts** — embedded in each test case as numbered, step-by-step instructions written in plain language
5. **Test Defect Reports** — logged in the Notes column of each test case; critical defects should also be filed in the project issue tracker with steps to reproduce
6. **Test Results** — captured by filling in the "Actual Result" and "Status" columns in `Test_Cases.md` during execution
7. **Test Evaluation Report** — a short summary document produced after all test cases are executed, covering: total test cases run, pass/fail counts by module, list of outstanding defects, and a go/no-go recommendation

---

## 8. Testing Tasks

Testing will be carried out in the following order:

1. **Set up the test environment** — ensure the FastAPI backend is running on port 8000, the React frontend is running on port 5173 (or 4173 for preview), and Ollama is running with the `qwen3:1.7b` model pulled
2. **Prepare test data** — upload `data/synthetic_2022_2025.csv` via the CSV upload feature on the Data Entry page; verify that all 48 rows appear in the Entry History table
3. **Execute Data Entry test cases** — run TC-001 through TC-050 (New Reading, CSV Upload, Train Model, Edit, Delete, Pagination, Clear All Data)
4. **Execute Forecast test cases** — run TC-051 through TC-061 (horizon selection, chart display, error states)
5. **Execute Ask WATT-IF test cases** — run TC-062 through TC-072 (chat submission, history, clear, offline behavior)
6. **Execute Price Calculator test cases** — run TC-073 through TC-083 (input handling, rate loading, bracket selection, bill breakdown)
7. **Execute Dashboard test cases** — run TC-084 through TC-092 (stat cards, anomaly card, chart, loading skeleton)
8. **Execute UI/UX test cases** — run TC-093 through TC-103 (dark mode, sidebar, mobile, health indicator, offline banner)
9. **Log defects** — record all failures in the Notes column and file detailed defect reports in the issue tracker
10. **Re-test defects after fixes** — once a developer has addressed a defect, re-run the corresponding test case and update the Status column
11. **Compile test evaluation report** — summarize results, list any outstanding defects, and provide a recommendation on release readiness
