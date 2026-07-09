# RACI Matrix — WATT-IF

**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## 1. Introduction

This document defines the RACI (Responsible, Accountable, Consulted, Informed) matrix for the WATT-IF project, organized by major project milestones and their corresponding tasks.

### RACI Definitions

| Letter | Role | Description |
|--------|------|-------------|
| **R** | Responsible | Person(s) who do the work to complete the task |
| **A** | Accountable | Person who is ultimately answerable for the task (one per task) |
| **C** | Consulted | Person(s) whose input is sought before a decision or action |
| **I** | Informed | Person(s) who are kept up-to-date on progress or decisions |

### Team Roles

| Role | Abbreviation |
|------|--------------|
| Project Manager | PM |
| Backend Developer | BE |
| Frontend Developer | FE |
| Data Scientist / ML Engineer | DS |
| QA Engineer | QA |
| UX Designer | UX |

---

## 2. RACI Matrix by Milestone

### Milestone 1: Planning

| Task | PM | BE | FE | DS | QA | UX |
|------|----|----|----|----|----|----|
| 1.1 Draft the Project Proposal | R/A | C | C | C | I | I |
| 1.2 Submission of Project Proposal | R/A | I | I | I | I | I |
| 1.3 Revision of Project Proposal | R/A | C | C | C | I | C |
| 1.4 Define Functional & Non-Functional Requirements | R/A | C | C | C | C | C |
| 1.5 Define system architecture & tech stack | A | R | R | R | I | I |
| 1.6 Define project timeline & milestones | R/A | C | C | C | C | I |

### Milestone 2: Data Preparation

| Task | PM | BE | FE | DS | QA | UX |
|------|----|----|----|----|----|----|
| 2.1 Identify and collect data sources (Meralco rates, weather, ENSO) | I | R | I | R/A | I | I |
| 2.2 Design database schema (SQLite tables, migrations) | I | R/A | I | C | I | I |
| 2.3 Build synthetic dataset generator (2022–2025) | I | C | I | R/A | I | I |
| 2.4 Implement data cleaning & imputation pipeline | I | R | I | R/A | I | I |
| 2.5 Implement CSV upload parsing & validation | I | R/A | I | C | C | I |
| 2.6 Build external data scrapers (Meralco PDF, Open-Meteo, NOAA) | I | R/A | I | C | I | I |
| 2.7 Perform Exploratory Data Analysis (EDA) | I | I | I | R/A | I | I |
| 2.8 Generate & ingest EDA summaries into ChromaDB | I | R | I | R/A | I | I |

### Milestone 3: Model Building

| Task | PM | BE | FE | DS | QA | UX |
|------|----|----|----|----|----|----|
| 3.1 Design SARIMAX model architecture (9 exogenous variables) | I | C | I | R/A | I | I |
| 3.2 Implement auto_arima order selection | I | C | I | R/A | I | I |
| 3.3 Implement training pipeline (80/10/10 split) | I | R | I | R/A | I | I |
| 3.4 Implement forecast generation (1/3/6/9/12 months) | I | R | I | R/A | I | I |
| 3.5 Implement month-aware fallback exogenous logic | I | R | I | R/A | I | I |
| 3.6 Implement confidence interval calculation (95% CI) | I | C | I | R/A | I | I |
| 3.7 Implement model evaluation metrics (MAPE, accuracy rating) | I | C | I | R/A | C | I |
| 3.8 Implement model persistence & backup (joblib) | I | R/A | I | C | I | I |
| 3.9 Configure RAG pipeline (ChromaDB + Ollama Qwen3 1.7B) | I | R/A | I | C | I | I |
| 3.10 Implement RAG scope filtering & prompt engineering | I | R | I | R/A | I | I |

### Milestone 4: System Development

| Task | PM | BE | FE | DS | QA | UX |
|------|----|----|----|----|----|----|
| 4.1 Design the User Interface (wireframes, tokens, themes) | I | I | C | I | I | R/A |
| 4.2 Develop Authentication module (register, login, JWT, rate limiting) | I | R/A | R | I | C | I |
| 4.3 Develop Data Entry module (manual entry, live preview, exog resolution) | I | R/A | R | I | C | C |
| 4.4 Develop CSV Upload module (upload, clean, report) | I | R/A | R | I | C | I |
| 4.5 Develop Entry History module (pagination, inline edit/delete) | I | R | R/A | I | C | C |
| 4.6 Develop Forecast module (charts, CI bands, tooltips, persistence) | I | R | R/A | C | C | C |
| 4.7 Develop RAG Chat module (streaming SSE, history, clear) | I | R/A | R | I | C | C |
| 4.8 Develop Price Calculator module (rate fetch, brackets, breakdown) | I | R/A | R | I | C | C |
| 4.9 Develop Dashboard module (stat cards, anomaly, charts, states) | I | I | R/A | I | C | R |
| 4.10 Develop Settings module (preferences, thresholds, data controls) | I | R | R/A | I | C | C |
| 4.11 Develop Navigation & App Shell (sidebar, routing, drawer, focus trap) | I | I | R/A | I | C | R |
| 4.12 Develop Health Monitoring module (endpoint, indicator, polling) | I | R/A | R | I | C | I |
| 4.13 Implement Per-User Data Isolation (scoped queries, ownership) | I | R/A | I | I | C | I |
| 4.14 Implement PWA features (service worker, offline cache, manifest) | I | I | R/A | I | C | I |
| 4.15 Implement Design Token System (CSS variables, dark/light themes) | I | I | R/A | I | I | R |
| 4.16 Implement Clear All Data feature (confirmation, wipe, cascade) | I | R | R/A | I | C | I |

### Milestone 5: Testing

| Task | PM | BE | FE | DS | QA | UX |
|------|----|----|----|----|----|----|
| 5.1 Write Test Plan & Test Cases (14 modules, 100+ cases) | I | C | C | C | R/A | I |
| 5.2 Create Selenium Automation Scripts (Page Objects, fixtures) | I | C | C | I | R/A | I |
| 5.3 Execute Automation Scripts | I | I | I | I | R/A | I |
| 5.4 Perform Integration Testing (API + frontend end-to-end) | I | R | R | I | R/A | I |
| 5.5 Perform Unit Testing (vitest, pytest, property-based tests) | I | R | R | R | A | I |
| 5.6 Perform Model Validation Testing (MAPE thresholds, edge cases) | I | I | I | R | A | I |
| 5.7 Perform UI/UX Testing (responsive, dark mode, accessibility) | I | I | C | I | R/A | C |
| 5.8 Perform Security Testing (auth bypass, injection, rate limiting) | I | R | I | I | R/A | I |
| 5.9 Bug fixing & regression testing | I | R | R | R | A | I |

### Milestone 6: Deployment

| Task | PM | BE | FE | DS | QA | UX |
|------|----|----|----|----|----|----|
| 6.1 Configure production environment (.env, secrets, CORS) | A | R | R | I | I | I |
| 6.2 Build production frontend bundle (Vite build, PWA assets) | I | I | R/A | I | I | I |
| 6.3 Configure local network access (LAN IP, host 0.0.0.0) | I | R/A | R | I | I | I |
| 6.4 Verify PWA installability (desktop + mobile) | I | I | R | I | R/A | I |
| 6.5 Final smoke test on deployed environment | A | C | C | I | R | I |
| 6.6 Prepare deployment guide & user manual | A | R | R | C | I | I |

### Milestone 7: Review / Documentation

| Task | PM | BE | FE | DS | QA | UX |
|------|----|----|----|----|----|----|
| 7.1 Compile final project documentation | R/A | C | C | C | C | C |
| 7.2 Write Requirements Traceability Matrix | R/A | C | C | C | R | I |
| 7.3 Finalize Test Results & QA Report | I | I | I | I | R/A | I |
| 7.4 Conduct project retrospective | R/A | R | R | R | R | R |
| 7.5 Prepare project presentation / demo | R/A | R | R | R | C | C |
| 7.6 Submit final deliverables | R/A | I | I | I | I | I |
| 7.7 Archive source code & documentation | R/A | R | R | I | I | I |

---

## 3. Summary — Milestone Ownership

| Milestone | Primary Accountable | Key Responsible |
|-----------|--------------------|-----------------| 
| 1. Planning | PM | PM, BE, FE, DS |
| 2. Data Preparation | DS | DS, BE |
| 3. Model Building | DS | DS, BE |
| 4. System Development | PM | BE, FE, UX |
| 5. Testing | QA | QA, BE, FE, DS |
| 6. Deployment | PM | BE, FE, QA |
| 7. Review / Documentation | PM | All |
