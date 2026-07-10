# WATT-IF Test Plan

**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

## 1. Introduction

WATT-IF is a locally-hosted Progressive Web App (PWA) that helps Philippine households forecast their monthly electricity consumption and bills. It connects to a FastAPI backend running on the user's own machine, using a SARIMAX model for forecasting, a RAG-powered chat assistant (via Ollama), and live Meralco rate data for bill calculations.

This test plan defines the scope, approach, and schedule for manual functional testing of the WATT-IF web application.

**Scope:** Manual black-box functional testing covering all 7 modules of the system. Backend internals, ML model accuracy, and automated performance benchmarks are explicitly out of scope.

**Intended audience:** Project stakeholders, developers, and testers involved in the WATT-IF project.

---

## 2. Module Structure

Testing is organized around the 7 system modules:

| Module | Test Prefix | Test Cases |
|--------|-------------|------------|
| 1. Account System | ACT | ACT-01 through ACT-22 |
| 2. Data Management | DM | DM-01 through DM-40 |
| 3. Forecasting & Dashboard | FD | FD-01 through FD-20 |
| 4. Chat Assistant | CHT | CHT-01 through CHT-11 |
| 5. Price Calculator | PCT | PCT-01 through PCT-13 |
| 6. Settings | SET | SET-01 through SET-16 |
| 7. System & Infrastructure | SYS | SYS-01 through SYS-11 |

---

## 3. Test Items

The following screens, forms, and components are in scope:

**Module 1 — Account System:**
- Registration form, Login form, Logout action, Session persistence, Data isolation behavior, Change password form

**Module 2 — Data Management:**
- New Reading form (month picker, kWh input, overrides, live bill preview)
- CSV Upload (file selector, upload result)
- Train Model button (status display, model info panel)
- Entry History table (pagination, inline edit/delete)
- Clear All Data button (confirmation panel)

**Module 3 — Forecasting & Dashboard:**
- Forecast page (horizon selector, kWh bar chart, bill line chart, CI display)
- Dashboard (stat cards, anomaly card, forecast chart, loading/empty states)

**Module 4 — Chat Assistant:**
- Ask WATT-IF page (message input, streaming response, Clear Chat button)

**Module 5 — Price Calculator:**
- kWh input, customer type selector, bracket selector, bill breakdown table, rate refresh button

**Module 6 — Settings:**
- Customer type, forecast horizon, rate override, chat preferences, notification thresholds, model retraining, data/privacy controls

**Module 7 — System & Infrastructure:**
- Dark/light mode toggle, sidebar navigation, mobile hamburger menu, health indicator, offline banner

---

## 4. Features to Be Tested

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
- Model training: trigger with sufficient/insufficient data, status transitions, model info update, concurrent training prevention
- Entry History: inline edit (valid/invalid), delete with confirmation, cancel edit, pagination (10/page), page navigation
- Clear All Data: confirmation, confirmed clear, cancelled clear, effect on model, re-upload after clear

### Module 3: Forecasting & Dashboard
- Horizon selection (1/3/6/9/12 months), chart update, data anchoring from latest entry
- kWh bar chart with error bars, bill line chart with CI band, tooltip on hover
- Error/empty states (no model, no data)
- Stat cards (correct values), anomaly detection, loading skeleton, empty state

### Module 4: Chat Assistant
- Question submission (button + Enter), empty message prevention, streaming response
- Input limit (500 chars), out-of-scope question handling
- History persistence, loading on mount, Clear Chat
- Ollama offline error handling

### Module 5: Price Calculator
- Valid/invalid kWh input, boundary values, rate loading, fallback when API unavailable
- Auto bracket selection, manual override, customer type change
- Bill breakdown correctness, rate refresh

### Module 6: Settings
- Customer type, forecast horizon, rate override (with boundaries), chat preferences
- Notification thresholds, model retraining options, data/privacy controls
- Input boundaries, persistence across navigation/refresh

### Module 7: System & Infrastructure
- Dark/light mode toggle + persistence, sidebar navigation, active item highlighting
- Mobile hamburger menu, overlay dismiss, Escape close
- Health indicator (all green, degraded), offline banner

---

## 5. Features Not to Be Tested

- Internal ML model accuracy (MAPE benchmarks, residual analysis)
- Ollama LLM response quality (factual correctness)
- Third-party API reliability (Meralco, Open-Meteo, NOAA uptime)
- Cross-browser compatibility beyond Chrome and Safari
- Security penetration testing
- Automated performance benchmarks

---

## 6. Approach

Testing follows a **black-box** approach: testers interact with the application as an end user without source code knowledge.

Three techniques are applied across all modules:

1. **Valid input testing** — confirm correct inputs produce expected outputs
2. **Invalid input testing** — confirm incorrect inputs are handled gracefully
3. **Boundary value analysis** — test at the edges of accepted ranges

---

## 7. Pass/Fail Criteria

| Area | Pass | Fail |
|------|------|------|
| Forms | Valid inputs accepted; invalid inputs show clear errors; no data saved for invalid inputs | Accepts invalid input, rejects valid input, or crashes |
| Charts | Data renders correctly; values match forecast data | Blank, error, or incorrect values |
| CRUD | Create/read/update/delete reflect immediately in UI | Silent failure, stale data, or unhandled error |
| Chat | Messages sent; responses stream and complete; history loads | Send failure, no response, or crash |
| Price Calculator | Breakdown matches expected calculation | Incorrect values or total mismatch |
| Auth | Registration creates account; login grants access; logout clears session; data isolated per user | Duplicate email allowed, info leaked, or cross-user access |
| General | — | Any unhandled exception, blank screen, or crash is automatic fail |

---

## 8. Test Deliverables

1. **Test Plan** *(this document)*
2. **Test Cases** — separate documents per module (TC_ACT, TC_DM, TC_FD, TC_CHT, TC_PCT, TC_SET, TC_SYS)
3. **Test Data** — `data/synthetic_2022_2025.csv` plus manual entry values in test cases
4. **Test Results** — captured in "Actual Result" and "Status" columns during execution
5. **Test Evaluation Report** — summary of pass/fail counts, outstanding defects, go/no-go recommendation

---

## 9. Testing Tasks (Execution Order)

1. Set up test environment (backend port 8000, frontend port 5173, Ollama with qwen3:1.7b)
2. Prepare test data (upload `data/synthetic_2022_2025.csv`)
3. Execute **Module 1: Account System** test cases (ACT-01 to ACT-22)
4. Execute **Module 2: Data Management** test cases (DM-01 to DM-40)
5. Execute **Module 3: Forecasting & Dashboard** test cases (FD-01 to FD-20)
6. Execute **Module 4: Chat Assistant** test cases (CHT-01 to CHT-11)
7. Execute **Module 5: Price Calculator** test cases (PCT-01 to PCT-13)
8. Execute **Module 6: Settings** test cases (SET-01 to SET-16)
9. Execute **Module 7: System & Infrastructure** test cases (SYS-01 to SYS-11)
10. Log defects and re-test after fixes
11. Compile test evaluation report

---

## 10. Suspension & Resumption Criteria

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

## 11. Roles and Responsibilities

| Role | Responsibilities |
|------|-----------------|
| UI/UX Designer | Test visual layout, component alignment, responsive design, dark/light mode |
| Project Manager | Oversee schedule, coordinate blockers, review final report, make go/no-go decision |
| Developer | Maintain test environment, investigate/fix defects, verify fixes |
| QA Lead | Own test plan/cases, assign execution, track results, compile evaluation report |
