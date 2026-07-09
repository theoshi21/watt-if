# WATT-IF Gantt Chart

**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## Project Timeline: June 2026 – July 2026 (8 Weeks)

### Legend

- `████` = Active work period
- `░░░░` = Buffer / overlap period
- W1–W4 = Weeks 1–4 of the month
- Person codes: PM, BE, FE, DS, QA, UX

---

## Gantt Chart

```
                              June 2026                    July 2026
Milestone / Task              W1    W2    W3    W4    W1    W2    W3    W4    Person Involved
─────────────────────────────────────────────────────────────────────────────────────────────

MILESTONE 1: PLANNING
─────────────────────────────────────────────────────────────────────────────────────────────
1.1 Draft Project Proposal    ████                                            PM
1.2 Submit Project Proposal   ████                                            PM
1.3 Revise Project Proposal         ████                                      PM, BE, DS
1.4 Define Functional &             ████                                      PM, BE, FE, DS
    Non-Functional Requirements
1.5 Define system architecture      ████                                      BE, FE, DS
    & tech stack
1.6 Define project timeline         ████                                      PM
    & milestones

MILESTONE 2: DATA PREPARATION
─────────────────────────────────────────────────────────────────────────────────────────────
2.1 Identify & collect data         ████  ████                                DS, BE
    sources (Meralco, weather,
    ENSO)
2.2 Design database schema                ████                                BE
    (SQLite, migrations)
2.3 Build synthetic dataset               ████                                DS
    generator (2022–2025)
2.4 Implement data cleaning &             ████                                DS, BE
    imputation pipeline
2.5 Implement CSV upload                  ████                                BE
    parsing & validation
2.6 Build external scrapers               ████  ████                          BE
    (Meralco PDF, Open-Meteo,
    NOAA)
2.7 Perform EDA                           ████                                DS
2.8 Generate & ingest EDA                       ████                          DS, BE
    summaries into ChromaDB

MILESTONE 3: MODEL BUILDING
─────────────────────────────────────────────────────────────────────────────────────────────
3.1 Design SARIMAX model                  ████                                DS
    architecture (9 exog vars)
3.2 Implement auto_arima                  ████  ████                          DS, BE
    order selection
3.3 Implement training pipeline                 ████                          DS, BE
    (80/10/10 split)
3.4 Implement forecast generation               ████                          DS, BE
    (1/3/6/9/12 months)
3.5 Implement month-aware                       ████                          DS, BE
    fallback exog logic
3.6 Implement confidence                        ████                          DS
    interval calculation (95% CI)
3.7 Implement model evaluation                  ████                          DS, QA
    metrics (MAPE, rating)
3.8 Implement model persistence                 ████                          BE
    & backup (joblib)
3.9 Configure RAG pipeline                      ████  ████                    BE, DS
    (ChromaDB + Ollama)
3.10 Implement RAG scope                              ████                    BE, DS
     filtering & prompt engineering
```

```
                              June 2026                    July 2026
Milestone / Task              W1    W2    W3    W4    W1    W2    W3    W4    Person Involved
─────────────────────────────────────────────────────────────────────────────────────────────

MILESTONE 4: SYSTEM DEVELOPMENT
─────────────────────────────────────────────────────────────────────────────────────────────
4.1 Design UI (wireframes,                ████                                UX, FE
    tokens, themes)
4.2 Develop Authentication                ████  ████                          BE, FE
    (register, login, JWT)
4.3 Develop Data Entry module                   ████                          BE, FE
    (manual entry, live preview)
4.4 Develop CSV Upload module                   ████                          BE, FE
    (upload, clean, report)
4.5 Develop Entry History                       ████  ████                    BE, FE
    (pagination, edit/delete)
4.6 Develop Forecast module                     ████  ████                    BE, FE, DS
    (charts, CI, tooltips)
4.7 Develop RAG Chat module                           ████                    BE, FE
    (streaming, history, clear)
4.8 Develop Price Calculator                          ████                    BE, FE
    (rate fetch, brackets)
4.9 Develop Dashboard                                 ████                    FE, UX
    (stat cards, anomaly, charts)
4.10 Develop Settings                                 ████                    BE, FE
     (preferences, thresholds)
4.11 Develop Navigation &                             ████                    FE, UX
     App Shell (sidebar, routing)
4.12 Develop Health Monitoring                        ████                    BE, FE
     (endpoint, indicator)
4.13 Implement Per-User                   ████  ████                          BE
     Data Isolation
4.14 Implement PWA features                           ████                    FE
     (service worker, offline)
4.15 Implement Design Token               ████                                FE, UX
     System (CSS vars, themes)
4.16 Implement Clear All Data                         ████                    BE, FE

MILESTONE 5: TESTING
─────────────────────────────────────────────────────────────────────────────────────────────
5.1 Write Test Plan & Test                            ████  ████              QA
    Cases (14 modules)
5.2 Create Selenium Automation                              ████              QA, BE
    Scripts (Page Objects)
5.3 Execute Automation Scripts                              ████  ████        QA
5.4 Integration Testing                                     ████  ████        QA, BE, FE
    (API + frontend E2E)
5.5 Unit Testing (vitest,                       ████  ████                    BE, FE, DS
    pytest, property-based)
5.6 Model Validation Testing                          ████                    DS, QA
    (MAPE thresholds)
5.7 UI/UX Testing (responsive,                             ████              QA, UX
    dark mode, accessibility)
5.8 Security Testing (auth,                                 ████              QA, BE
    injection, rate limiting)
5.9 Bug fixing & regression                                 ████  ████        BE, FE, DS, QA

MILESTONE 6: DEPLOYMENT
─────────────────────────────────────────────────────────────────────────────────────────────
6.1 Configure production                                          ████        BE, FE
    environment (.env, CORS)
6.2 Build production frontend                                     ████        FE
    bundle (Vite, PWA assets)
6.3 Configure local network                                       ████        BE, FE
    access (LAN IP, host)
6.4 Verify PWA installability                                     ████        QA, FE
    (desktop + mobile)
6.5 Final smoke test                                              ████        QA
6.6 Prepare deployment guide                                      ████        BE, FE, PM

MILESTONE 7: REVIEW / DOCUMENTATION
─────────────────────────────────────────────────────────────────────────────────────────────
7.1 Compile final project                                               ████  PM, All
    documentation
7.2 Write Requirements                                                  ████  PM, QA
    Traceability Matrix
7.3 Finalize Test Results                                               ████  QA
    & QA Report
7.4 Conduct project                                                     ████  All
    retrospective
7.5 Prepare project                                                     ████  PM, BE, FE, DS
    presentation / demo
7.6 Submit final deliverables                                           ████  PM
7.7 Archive source code                                                 ████  PM, BE, FE
    & documentation
```

---

## Timeline Summary

| Milestone | Start | End | Duration |
|-----------|-------|-----|----------|
| 1. Planning | June W1 | June W2 | 2 weeks |
| 2. Data Preparation | June W2 | June W4 | 3 weeks |
| 3. Model Building | June W3 | July W1 | 3 weeks |
| 4. System Development | June W3 | July W2 | 4 weeks |
| 5. Testing | June W4 | July W3 | 4 weeks |
| 6. Deployment | July W3 | July W3 | 1 week |
| 7. Review / Documentation | July W4 | July W4 | 1 week |

---

## Dependencies & Notes

1. **Milestone 2 depends on Milestone 1** — Data preparation cannot begin until architecture and requirements are defined.
2. **Milestone 3 depends on Milestone 2** — Model building requires cleaned data and external integrations to be available.
3. **Milestone 4 overlaps with Milestones 2 & 3** — Frontend UI development (shell, design tokens) can start in parallel with backend data/model work.
4. **Milestone 5 overlaps with Milestone 4** — Unit tests are written alongside development; integration/automation testing starts once modules are complete.
5. **Milestone 6 depends on Milestones 4 & 5** — Deployment only occurs after development is complete and critical bugs are resolved.
6. **Milestone 7 depends on Milestone 6** — Final documentation is compiled after the system is deployed and validated.

---

## Critical Path

```
Planning → Data Preparation → Model Building → System Development (backend) → Testing → Deployment → Review
```

The critical path runs through the backend/ML pipeline. Frontend development runs in parallel but must integrate with backend APIs before testing begins.
