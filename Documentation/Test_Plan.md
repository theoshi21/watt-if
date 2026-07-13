# WATT-IF Test Plan

**Document Version:** 3.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

## 1. Introduction

WATT-IF is a locally-hosted Progressive Web App (PWA) that helps Philippine households forecast their monthly electricity consumption and bills. It connects to a FastAPI backend running on the user's own machine, using a SARIMAX model for forecasting, a RAG-powered chat assistant (via Ollama), and live Meralco rate data for bill calculations.

This test plan defines the scope, approach, and schedule for functional, security, performance, accessibility, and compatibility testing of the WATT-IF web application.

**Scope:** Black-box functional testing, security testing, performance testing, accessibility testing, and browser compatibility testing covering all 7 modules plus cross-cutting concerns.

**Intended audience:** Project stakeholders, developers, and testers involved in the WATT-IF project.

---

## 2. Module Structure

Testing is organized around 7 system modules plus 5 cross-cutting test areas:

### Functional Test Cases

| Module | Test Prefix | Test Cases |
|--------|-------------|------------|
| 1. Account System | ACT | ACT-01 through ACT-22 |
| 2. Data Management | DM | DM-01 through DM-46 |
| 3. Forecasting & Dashboard | FD | FD-01 through FD-26 |
| 4. Chat Assistant | CHT | CHT-01 through CHT-11 |
| 5. Price Calculator | PCT | PCT-01 through PCT-18 |
| 6. Settings | SET | SET-01 through SET-16 |
| 7. System & Infrastructure | SYS | SYS-01 through SYS-11 |

### Cross-Cutting Test Cases

| Area | Test Prefix | Test Cases |
|------|-------------|------------|
| Security Testing | SEC | SEC-01 through SEC-06 |
| Performance Testing | PERF | PERF-01 through PERF-06 |
| AI Robustness | AIR | AIR-01 through AIR-06 |
| Browser Compatibility | BRWS | BRWS-01 through BRWS-04 |
| Accessibility Testing | A11Y | A11Y-01 through A11Y-06 |

---

## 3. Naming Convention

All test cases follow a consistent prefixed identifier scheme:

```
<PREFIX>-<SEQUENTIAL_NUMBER>
```

| Prefix | Module/Area |
|--------|-------------|
| ACT | Account System |
| DM | Data Management |
| FD | Forecasting & Dashboard |
| CHT | Chat Assistant |
| PCT | Price Calculator |
| SET | Settings |
| SYS | System & Infrastructure |
| SEC | Security |
| PERF | Performance |
| AIR | AI Robustness |
| BRWS | Browser Compatibility |
| A11Y | Accessibility |

---

## 4. Test Items

The following screens, forms, fields, buttons, and components are in scope, organized by module.

---

### Module 1 — Account System

**Login Page (`/login`)**
- Email input (`#login-email`, type=email, required)
- Password input (`#login-password`, type=password, required)
- "Sign In" submit button (disabled while submitting)
- Error alert (`role="alert"`) for invalid credentials
- "Register" link → navigates to `/register`
- Redirect to `/` if already authenticated

**Register Page (`/register`)**
- Email input (`#register-email`, type=email, required)
- Password input (`#register-password`, type=password, required, min 8 chars)
- Confirm Password input (`#register-confirm-password`, type=password, required)
- Password length hint (shown when < 8 chars entered)
- Password mismatch hint (shown when confirm ≠ password)
- "Create Account" submit button (disabled until valid)
- Error alert (`role="alert"`) for duplicate email or API errors
- "Sign in" link → navigates to `/login`

**Change Password (on `/account`)**
- Current Password input (`#current-password`, type=password)
- New Password input (`#new-password`, type=password, aria-invalid on error)
- Confirm New Password input (`#confirm-password`, type=password, aria-invalid on error)
- "Update Password" submit button (disabled while submitting)
- Inline error messages (`#new-pw-err`, `#confirm-pw-err`)
- API error alert, success status message

**Logout**
- Logout button in sidebar (`aria-label="Logout"`)
- Logout button in Account Settings section (btn-danger style)

---

### Module 2 — Data Management

**New Reading Form (`/data-entry`)**
- Month selector: Month dropdown (`aria-label="Month"`, options Jan–Dec) + Year dropdown (`aria-label="Year"`, 10-year range)
- kWh input (`#r-kwh`, type=number, min=0, max=99999, step=any, required)
- kWh error message (`#kwh-err`, `role="alert"`)
- Live bill preview (shown when kWh > 0 and rate available, bill field empty)
- Optional Overrides section (`<details>` toggle):
  - Actual Bill Amount input (`#r-bill`, type=number, min=0, step=any, placeholder="Auto: kWh × rate")
  - Rate Override input (`#r-rate`, type=number, min=0, step=any, placeholder="Auto: live Meralco rate")
- "Submit" button (disabled while submitting)
- Submit error alert (`role="alert"`)

**Upload Bill Data Panel**
- "Choose CSV" label button (`htmlFor="csv-upload"`, disabled while uploading)
- Hidden file input (`#csv-upload`, type=file, accept=".csv")
- Upload status/result message (`role="status"` or `role="alert"`)

**Model Training Panel**
- "Train Model" button (btn-primary, disabled while running, shows "⚙ Training…")
- Training status display (Idle / ⚙ Training… / ✓ Done / ✗ Failed with color coding)
- Error message (`role="alert"`)
- Model info panel:
  - Last trained date
  - Training window (start–end months)
  - Avg MAPE % with rating badge (Good / Fair / Poor)

**Entry History Table**
- Table columns: Month, kWh, Bill (PHP), Source, Rate ₱/kWh (auto), Temp °C (auto), Humidity % (auto), Rain mm (auto), Hot Days (auto), Rainy Days (auto), Holidays (auto), Weekends (auto), ENSO badge (auto), Actions
- ENSO badge: El Niño (red), La Niña (green), Neutral (muted), — (null)
- Edit button per row (`aria-label="Edit {year_month}"`)
- Delete button per row (`aria-label="Delete {year_month}"`, shown in red)
- Inline edit row: kWh input, Bill input, Save button, Cancel button, error message
- Delete confirmation dialog (`role="alertdialog"`, `aria-modal="true"`): Yes/Cancel buttons
- Pagination controls: « ‹ page numbers › » buttons, page indicator text
- Entry count display (e.g. "42 entries")
- Empty state message when no entries

**Danger Zone**
- "Clear All Data…" button (btn-danger)
- Confirmation panel (red border, warning text): "Yes, clear everything" + "Cancel" buttons
- Error message on clear failure

---

### Module 3 — Forecasting & Dashboard

**Forecast Page (`/forecast`)**
- Horizon Selector (`role="group"`, `aria-label="Forecast horizon"`): 5 toggle buttons — 1 Mo, 3 Mo, 6 Mo, 9 Mo, 12 Mo (`aria-pressed`)
- Loading status (`role="status"`)
- Error alert (`role="alert"`) — including 503 "no model" message
- Budget Alerts panel (`role="alert"`, red left border): lists threshold warnings
- kWh Forecast Chart: bar chart with error bars (95% CI), X-axis (month labels), Y-axis (kWh), tooltip showing forecast + CI range
- Bill Forecast Chart: composed line+area chart, X-axis (month labels), Y-axis (₱), CI shaded area, tooltip showing price + CI range
- Empty state message when no forecast generated

**Dashboard Page (`/`)**
- Stat cards (4 cards):
  - "This Month" — kWh forecast value
  - "Daily Average" — kWh/day
  - "Avg Temp" — °C
  - "Avg Humidity" — %
- Anomaly Card (conditional): shown when first forecast month > 110% of mean
- "Consumption History" section heading
- ForecastChart component (same as Forecast page)
- Loading skeleton (4 card skeletons + 1 chart skeleton, `aria-hidden="true"`)
- Empty state card (message + link guidance to Data Entry)
- Error state card (red left border, error message)

---

### Module 4 — Chat Assistant

**Ask Page (`/ask`) — ChatPanel component**
- "Ask about your forecast" section heading
- "Clear chat" button (trash icon, disabled when no messages or loading, `aria-label="Clear conversation"`)
- Message thread (`role="log"`, `aria-live="polite"`, `aria-label="Conversation"`)
  - User message bubbles (right-aligned, accent color)
  - Assistant message bubbles (left-aligned, card color, markdown rendered)
  - Error message bubbles (red border)
  - "Generating answer…" typing indicator (animated bounce dots)
  - "Loading history…" state on mount
  - Empty state prompt ("Ask a question about your electricity forecast.")
- Question input (`aria-label="Question input"`, type=text, maxLength=500, disabled while loading)
- Character counter display (e.g. "42/500")
- "Ask" submit button (disabled when input empty or loading)
- History error message when chat history fails to load

---

### Module 5 — Price Calculator

**Price Calculator Page (`/calculator`)**
- Page title: "Bill Calculator"
- Rate status text: effective month + Live/Fallback badge
- "↻ Refresh Rate" button (btn-secondary, disabled while refreshing or loading)
- Rate loading status (`role="status"`)
- Rate error alert (`role="alert"`)
- "Account type" dropdown (`#customer-type`): Residential, General Service A, General Service B
- "Monthly consumption" input (`#calc-kwh`, type=number, min=0, max=99999, step=any, `aria-label="Monthly consumption in kWh"`)
- "Rate bracket" dropdown (`#bracket-select`): Auto-select + all bracket options (shown only when customer type has multiple brackets)
- Auto-bracket label (shows detected bracket when set to auto)
- Estimated Bill total card (accent color, shows ₱ total, kWh, effective rate, customer type + bracket)
- "Enter your monthly consumption" placeholder when no kWh entered
- Bill breakdown table (right panel): Generation, Transmission, System Loss, Distribution, Supply, Supply (fixed), Metering, Metering (fixed), UC/FIT/GEA/AWAT/Other, Total Amount Due — each with sublabel showing rate × kWh and VAT %
- Fallback rate warning (shown when `is_fallback = true`)
- Source link to Meralco Rates Archive
- Last fetched timestamp

---

### Module 6 — Settings

**Account Settings Page (`/account`)**
- Account section: Email display (read-only)
- Change Password form (described in Module 1)
- Customer Type section: dropdown (`#customer-type-select`, options: Residential / General Service A / General Service B, auto-saves on change)
- Default Forecast Horizon section: dropdown (`#horizon-select`, options: 1/3/6/9/12 months, auto-saves on change)
- Electricity Rate Override section: number input (`#rate-override-input`, type=number, step=0.01, min=0, max=100, placeholder="e.g. 11.80"), "Clear" button (shown only when override is set)
- Chat Preferences section:
  - Max messages shown input (`#chat-max-history`, type=number, min=10, max=500, step=10)
  - "Auto-clear chat on logout" toggle (`<input type="checkbox">` + toggle-slider)
- Notification Thresholds section:
  - Monthly kWh budget input (`#notify-kwh-budget`, type=number, min=0, max=99999, step=10)
  - Bill ceiling (₱) input (`#notify-bill-ceiling`, type=number, min=0, max=999999, step=100)
  - High consumption warning (kWh) input (`#notify-high-consumption`, type=number, min=0, max=99999, step=10)
- Model Retraining section:
  - "Auto-retrain on CSV upload" toggle (`<input type="checkbox">` + toggle-slider)
  - Minimum data points input (`#min-datapoints`, type=number, min=3, max=60, step=1)
  - Warning message when current entry count < minimum threshold
- Data & Privacy section:
  - "Clear Chat History" button → inline confirmation: "Yes, clear" + "Cancel"
  - "Clear All Data & Model" button (btn-danger) → inline confirmation: "Yes, delete all" + "Cancel"
- Global success toast (dismissible, `role="status"`)
- Global error message (`role="alert"`)
- Logout button (btn-danger, in Session section)

---

### Module 7 — System & Infrastructure

**TopBar (all authenticated pages)**
- Hamburger menu button (`aria-label="Open navigation menu"`, mobile only)
- Page title heading (dynamic per route)
- Dark Mode Toggle button
- User Account button (`aria-label="User account"`, navigates to `/account`)

**Sidebar**
- WATT-IF logo image (`alt="WATT-IF logo"`)
- "WATT-IF" name + "ENERGY INTELLIGENCE" subtitle
- Navigation links (`role="list"`): Dashboard, Forecast, Ask WATT-IF, Price Calculator, Data Entry — each with icon and active state highlight
- Health Indicator component
- Model Status Pill component
- User email display (truncated at 24 chars, `aria-label="Logged in as {email}"`)
- Logout button (`aria-label="Logout"`, with icon)

**Health Indicator**
- Status display: all-green (operational) or degraded states per subsystem

**Model Status Pill**
- Displays current training status

**Dark Mode Toggle**
- Button toggling light/dark theme, persists across sessions

**Mobile Navigation**
- Sidebar overlay on mobile (hamburger → opens, click outside or Escape → closes)

---

### Non-Functional Test Areas

**Security**
- SQL injection via all text/number input fields
- Cross-Site Scripting (XSS) via chat input, data entry labels, CSV content
- CSV injection (formula injection via cells beginning with `=`, `+`, `-`, `@`)
- Unauthorized API access (invalid Bearer token, missing token)
- Session timeout handling (expired JWT)
- Authentication bypass attempts

**Performance**
- CSV upload with 10,000+ rows
- Forecast generation under load
- 100 simultaneous users
- Concurrent model training requests
- Database with 1,000+ entries
- API response time benchmarks

**AI Robustness**
- Highly irregular historical data (random noise)
- Missing months in history
- Extreme outliers (e.g. 50,000 kWh)
- Negative forecast prevention
- CI anomalies (CI wider than forecast value)
- Model convergence failures

**Browser Compatibility**
- Google Chrome (latest stable)
- Mozilla Firefox (latest stable)
- Microsoft Edge (latest stable)
- Apple Safari (latest stable)

**Accessibility**
- Keyboard-only navigation (Tab, Enter, Escape, arrow keys)
- Screen reader (NVDA / VoiceOver)
- Color contrast (WCAG AA minimum, 4.5:1)
- Focus indicators on all interactive elements
- ARIA labels on custom controls and charts
- Accessible alternatives for chart data

---

## 5. Features to Be Tested

### Module 1: Account System
- Registration: valid email/password, duplicate email rejection, short password rejection, invalid email, mismatched confirmation
- Login: correct credentials, wrong password (generic error), non-existent email (same error), rate limiting after 10 failures
- Logout: token clearance, redirect to login, offline handling
- Session: token persistence across refresh, expired token re-login, API 401 clearance
- Data isolation: per-user entries, per-user chat, per-user model, cross-user access prevention (403)
- Password change: valid change, incorrect current password, mismatched new passwords

### Module 2: Data Management
- Manual entry: valid input acceptance, field validation (blank/zero/negative/non-numeric), live bill preview, duplicate month handling, optional overrides
- CSV upload: valid CSV (minimum + extended columns), invalid file types, missing columns, blank values (imputation), duplicate months, re-upload deduplication
- **CSV edge cases:** corrupted CSV file, empty CSV file, very large CSV (10,000+ rows), CSV with special characters, UTF-8 encoding issues, formula injection (cells beginning with `=`)
- Model training: trigger with sufficient/insufficient data, status transitions, model info update, concurrent training prevention, interrupted training process
- Entry History: inline edit (valid/invalid), delete with confirmation, cancel edit, pagination (10/page), page navigation
- Clear All Data: confirmation, confirmed clear, cancelled clear, effect on model, re-upload after clear

### Module 3: Forecasting & Dashboard
- Horizon selection (1/3/6/9/12 months), chart update, data anchoring from latest entry
- kWh bar chart with error bars, bill line chart with CI band, tooltip on hover
- Error/empty states (no model, no data)
- Stat cards (correct values), anomaly detection, loading skeleton, empty state
- **Edge cases:** extremely noisy datasets, missing historical months, outlier consumption values, failed model convergence, forecast API timeout, simultaneous dashboard refreshes, slow API responses, cached vs. live data, partial data loading

### Module 4: Chat Assistant
- Question submission (button + Enter), empty message prevention, streaming response
- Input limit (500 chars), out-of-scope question handling
- History persistence, loading on mount, Clear Chat
- Ollama offline error handling

### Module 5: Price Calculator
- Valid/invalid kWh input, boundary values, rate loading, fallback when API unavailable
- Auto bracket selection, manual override, customer type change
- Bill breakdown correctness, rate refresh
- **Edge cases:** decimal kWh values, invalid currency format, API timeout while retrieving rates, negative rate values, missing rate service

### Module 6: Settings
- Customer type, forecast horizon, rate override (with boundaries), chat preferences
- Notification thresholds, model retraining options, data/privacy controls
- Input boundaries, persistence across navigation/refresh

### Module 7: System & Infrastructure
- Dark/light mode toggle + persistence, sidebar navigation, active item highlighting
- Mobile hamburger menu, overlay dismiss, Escape close
- Health indicator (all green, degraded), offline banner

### Cross-Cutting: Security
- SQL injection via input fields
- Cross-Site Scripting (XSS) via text inputs
- CSV injection (formula injection via uploaded data)
- Unauthorized API access (invalid/missing tokens)
- Session timeout handling
- Authentication bypass attempts

### Cross-Cutting: Performance
- Uploading very large CSV files (10,000+ rows)
- Forecast generation under heavy load
- 100 simultaneous users
- Multiple concurrent model training requests
- Large database performance (1,000+ entries)
- API response time benchmarks

### Cross-Cutting: AI Robustness
- Highly irregular historical data (random noise)
- Missing months in historical data
- Extreme outliers (e.g., 50,000 kWh in one month)
- Negative forecast prevention
- Confidence interval anomalies (CI wider than value)
- Model convergence failures

### Cross-Cutting: Browser Compatibility
- Google Chrome (latest stable)
- Mozilla Firefox (latest stable)
- Microsoft Edge (latest stable)
- Apple Safari (latest stable)

### Cross-Cutting: Accessibility
- Keyboard-only navigation (Tab, Enter, Escape)
- Screen reader compatibility (NVDA/VoiceOver)
- Color contrast ratios (WCAG AA minimum)
- Focus indicators on all interactive elements
- ARIA labels on custom components
- Accessible chart alternatives

---

## 6. Features Not to Be Tested

- Internal ML model accuracy (MAPE benchmarks, residual analysis)
- Ollama LLM response quality (factual correctness)
- Third-party API reliability (Meralco, Open-Meteo, NOAA uptime)
- Security penetration testing (professional pen test)
- Load testing beyond 100 concurrent users
- iOS PWA install (requires HTTPS)

---

## 7. Approach

Testing follows a **black-box** approach: testers interact with the application as an end user without source code knowledge.

Techniques applied across all modules:

1. **Valid input testing** — confirm correct inputs produce expected outputs
2. **Invalid input testing** — confirm incorrect inputs are handled gracefully
3. **Boundary value analysis** — test at the edges of accepted ranges
4. **Error guessing** — test common failure modes (network loss, timeouts, corrupted input)
5. **Security probing** — test for injection, unauthorized access, and session vulnerabilities
6. **Compatibility testing** — verify functionality across supported browsers
7. **Accessibility testing** — verify WCAG compliance and assistive technology compatibility

---

## 8. Pass/Fail Criteria

| Area | Pass | Fail |
|------|------|------|
| Forms | Valid inputs accepted; invalid inputs show clear errors; no data saved for invalid inputs | Accepts invalid input, rejects valid input, or crashes |
| Charts | Data renders correctly; values match forecast data | Blank, error, or incorrect values |
| CRUD | Create/read/update/delete reflect immediately in UI | Silent failure, stale data, or unhandled error |
| Chat | Messages sent; responses stream and complete; history loads | Send failure, no response, or crash |
| Price Calculator | Breakdown matches expected calculation | Incorrect values or total mismatch |
| Auth | Registration creates account; login grants access; logout clears session; data isolated per user | Duplicate email allowed, info leaked, or cross-user access |
| Security | Injection attempts rejected; unauthorized access returns 401/403; sessions expire correctly | Injection succeeds, data exposed, or sessions persist indefinitely |
| Performance | Operations complete within acceptable time; no crashes under load | Timeout, crash, or memory exhaustion |
| AI Robustness | Model handles edge-case data gracefully; errors reported clearly | Crash, negative forecasts, or unhandled exceptions |
| Browser Compat | Core functionality works identically across all tested browsers | Layout broken, features missing, or JS errors in any browser |
| Accessibility | All interactive elements keyboard-accessible; proper ARIA labels; sufficient contrast | Unreachable elements, missing labels, or insufficient contrast |
| General | — | Any unhandled exception, blank screen, or crash is automatic fail |

---

## 9. Test Deliverables

1. **Test Plan** *(this document)*
2. **Test Cases** — separate documents per module (TC_ACT, TC_DM, TC_FD, TC_CHT, TC_PCT, TC_SET, TC_SYS) plus cross-cutting (TC_SEC, TC_PERF, TC_AIR, TC_BRWS, TC_A11Y)
3. **Test Data** — `data/synthetic_2022_2025.csv` plus manual entry values in test cases
4. **Test Results** — captured in "Actual Result" and "Status" columns during execution
5. **Test Evaluation Report** — summary of pass/fail counts, outstanding defects, go/no-go recommendation

---

## 10. Testing Tasks (Execution Order)

1. Set up test environment (backend port 8000, frontend port 5173, Ollama with qwen3:1.7b)
2. Prepare test data (upload `data/synthetic_2022_2025.csv`)
3. Execute **Module 1: Account System** test cases (ACT-01 to ACT-22)
4. Execute **Module 2: Data Management** test cases (DM-01 to DM-46)
5. Execute **Module 3: Forecasting & Dashboard** test cases (FD-01 to FD-26)
6. Execute **Module 4: Chat Assistant** test cases (CHT-01 to CHT-11)
7. Execute **Module 5: Price Calculator** test cases (PCT-01 to PCT-18)
8. Execute **Module 6: Settings** test cases (SET-01 to SET-16)
9. Execute **Module 7: System & Infrastructure** test cases (SYS-01 to SYS-11)
10. Execute **Security** test cases (SEC-01 to SEC-06)
11. Execute **Performance** test cases (PERF-01 to PERF-06)
12. Execute **AI Robustness** test cases (AIR-01 to AIR-06)
13. Execute **Browser Compatibility** test cases (BRWS-01 to BRWS-04)
14. Execute **Accessibility** test cases (A11Y-01 to A11Y-06)
15. Log defects and re-test after fixes
16. Compile test evaluation report

---

## 11. Suspension & Resumption Criteria

**Suspend when:**
- A defect blocks a significant portion of test cases (e.g., backend won't start, frontend broken)
- A critical data-loss bug is found
- The test environment becomes unstable
- More than 20% of a module's tests fail due to the same root cause

**Resume when:**
- The blocking defect is fixed and verified
- The test environment is reset to a clean state
- The QA Lead confirms stability

---

## 12. Roles and Responsibilities

| Role | Responsibilities |
|------|-----------------|
| UI/UX Designer | Test visual layout, component alignment, responsive design, dark/light mode, accessibility |
| Project Manager | Oversee schedule, coordinate blockers, review final report, make go/no-go decision |
| Developer | Maintain test environment, investigate/fix defects, verify fixes, support performance testing |
| QA Lead | Own test plan/cases, assign execution, track results, compile evaluation report |

---

## 13. Test Environment

| Component | Configuration |
|-----------|---------------|
| Backend | FastAPI on `http://localhost:8000` |
| Frontend (dev) | Vite on `http://localhost:5173` |
| Frontend (prod) | Vite preview on `http://localhost:4173` |
| LLM Service | Ollama on `http://localhost:11434` with `qwen3:1.7b` |
| Database | SQLite at `data/wattif.db` |
| Vector Store | ChromaDB at `data/chroma/` |
| Browsers | Chrome (latest), Firefox (latest), Edge (latest), Safari (latest) |
| OS | Windows 10/11 |
| Test Data | `data/synthetic_2022_2025.csv` (48 months, 2022–2025) |
