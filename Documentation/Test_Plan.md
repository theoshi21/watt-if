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
- **Registration form** (Registration page) — email input, password input, confirm-password input, submit button, validation messages
- **Login form** (Login page) — email input, password input, submit button, error display, link to Registration
- **Logout action** (Sidebar) — logout button, token clearance, redirect to Login
- **Session persistence mechanism** — JWT token storage in localStorage, token validation on page load, automatic re-login for Default Account
- **Data isolation behavior** — per-user bill records, per-user trained model, per-user chat history, cross-user access prevention
- **Settings page** (Account/Settings page) — customer type dropdown, default forecast horizon dropdown, rate override input, chat max history input, chat auto-clear toggle, notification threshold inputs (kWh budget, bill ceiling, high consumption), auto-retrain toggle, minimum data points input, clear chat button, clear all data button

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

### Account System
- Registration: valid email and password creates account, duplicate email rejected, password under 8 chars rejected, invalid email format rejected, mismatched confirm-password prevents submission
- Login: correct credentials grant access, wrong password shows generic error, non-existent email shows same generic error, rate limiting after 10 failed attempts
- Logout: token cleared from localStorage, redirect to Login page, graceful handling when network is unavailable
- Session persistence: token survives page refresh, expired token forces re-login, API 401 triggers session clearance
- Data isolation: users cannot see each other's data entries, chat history is per-user, trained models are per-user, cross-user edit/delete returns 403
- Error handling: unauthenticated access redirects to Login, authenticated users cannot access Login/Register pages, password change validates current password, password change validates new password requirements

### UI/UX
- Dark/light mode: toggle switches theme, preference persists after reload
- Sidebar navigation: each link navigates to the correct page, active item highlighted
- Mobile responsiveness: hamburger menu opens/closes sidebar, overlay tap and Escape key close sidebar
- Health indicator: all-green when all systems up, degraded when Ollama is offline
- Offline banner: appears when network connection is lost

### Settings
- Customer type: dropdown saves selection, persists after page reload, pre-selects in Price Calculator
- Default forecast horizon: dropdown saves selection, pre-selects in Forecast page on fresh load
- Rate override: accepts valid ₱/kWh values (0–100), clears correctly, used in data entry resolution
- Chat preferences: max history accepts 10–500, auto-clear toggle saves correctly
- Data & privacy: clear chat requires confirmation and wipes chat, clear all requires confirmation and wipes everything
- Notification thresholds: kWh budget (0–99,999), bill ceiling (0–999,999), and high consumption (0–99,999) save correctly
- Model retraining: auto-retrain toggle saves, min data points accepts 3–60, retrain endpoint respects minimum
- Input boundaries: all numeric inputs enforce min/max limits, values cannot go beyond screen
- Settings persistence: all changes persist after page navigation and refresh
- Settings API: GET /settings returns defaults for new user, PUT /settings accepts partial updates

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
| **Account/Authentication** | Registration creates account and auto-logs in; login returns valid JWT; logout clears token and redirects; session persists across refresh; each user sees only their own data entries, models, and chat history; cross-user access returns 403 | Registration allows duplicate emails; login leaks whether email exists; logout leaves token in storage; expired token grants access; one user's data is visible to another; cross-user mutation succeeds |

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
9. **Execute Account System test cases** — run ACT-01 through ACT-22 (registration, login, logout, session persistence, data isolation, error handling)
10. **Execute Settings test cases** — run SET-01 through SET-15 (customer type, forecast horizon, rate override, chat preferences, notifications, model retraining, data privacy)
11. **Log defects** — record all failures in the Notes column and file detailed defect reports in the issue tracker
12. **Re-test defects after fixes** — once a developer has addressed a defect, re-run the corresponding test case and update the Status column
13. **Compile test evaluation report** — summarize results, list any outstanding defects, and provide a recommendation on release readiness

---

## 9. Suspension Criteria and Resumption Requirements

*When to stop and when to resume testing*

Testing will be **suspended** when any of the following conditions are met:

- A defect is discovered that blocks a significant portion of the test cases from being executed (e.g., the FastAPI backend fails to start, the frontend build is broken, or the CSV upload is non-functional)
- A critical data-loss bug is found that could corrupt the test database or wipe entries unexpectedly during a test run
- The test environment becomes unstable (e.g., Ollama repeatedly crashes, the SQLite database becomes locked, or the frontend cannot connect to the backend)
- More than 20% of test cases in a single module result in a Fail status due to the same underlying defect, making further execution of that module meaningless

When suspension occurs, all affected test cases are marked **Blocked** and the blocking defect is filed in the issue tracker with full reproduction steps. Testing of unaffected modules may continue in parallel at the tester's discretion.

Testing will **resume** when:

- The blocking defect has been fixed and a new build is available for testing
- The fix has been verified by the developer and the test environment has been reset to a clean state (data wiped and re-uploaded from `data/synthetic_2022_2025.csv` where necessary)
- The QA Lead has confirmed the environment is stable before re-executing the blocked test cases

---

## 10. Roles and Responsibilities

*Who is to carry out what task*

| Role | Assigned | Responsibilities |
|---|---|---|
| **UI/UX Designer** | *(TBD)* | Test the visual layout, component alignment, and interactive behavior of all UI elements; verify dark/light mode, responsive design, and sidebar navigation; flag any design inconsistencies against the approved mockups |
| **Project Manager** | *(TBD)* | Oversee the overall testing schedule and ensure milestones are met; coordinate between team members when blockers arise; review and sign off on the final Test Evaluation Report; make the go/no-go recommendation for release |
| **Developer** | *(TBD)* | Set up and maintain the test environment (backend, frontend, Ollama); investigate and fix defects filed during testing; verify fixes locally before marking defects as resolved; support testers with environment issues |
| **QA Lead** | *(TBD)* | Own the test plan and test cases; assign test cases to team members; track pass/fail counts and outstanding defects; enforce suspension and resumption criteria; compile the Test Evaluation Report after all test cases are executed |
