# Non-Functional Requirements — WATT-IF

**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## 1. Introduction

This document defines the non-functional requirements (quality attributes) for WATT-IF, organized to complement the 7-module functional structure. These requirements specify constraints on performance, security, usability, reliability, maintainability, portability, and data integrity.

---

## 2. Performance

| ID | Requirement |
|----|-------------|
| NFR-01 | API endpoints (excluding training) SHALL respond within 2 seconds under normal load. |
| NFR-02 | Forecast generation SHALL complete within 10 seconds for any valid horizon. |
| NFR-03 | Model training SHALL complete within 120 seconds for datasets up to 60 data points. |
| NFR-04 | RAG chat SHALL begin streaming the first token within 15 seconds. |
| NFR-05 | Frontend initial page load (LCP) SHALL complete within 3 seconds on localhost. |
| NFR-06 | Meralco rate PDF parse SHALL complete within 30 seconds; cached results in under 100ms. |
| NFR-07 | CSV upload processing SHALL complete within 30 seconds for files up to 10 MB. |
| NFR-08 | Paginated queries SHALL execute within 500ms regardless of total record count. |
| NFR-09 | The Ollama LLM SHALL be warmed up on startup to reduce first-query latency. |

---

## 3. Security

| ID | Requirement |
|----|-------------|
| NFR-10 | Passwords SHALL be hashed with bcrypt (cost factor ≥ 12). |
| NFR-11 | JWT tokens SHALL use HS256, expire after 24 hours, and include sub/email/exp/iat claims. |
| NFR-12 | The JWT secret SHALL be configurable via environment variable; not hardcoded in production. |
| NFR-13 | Timing-attack mitigation SHALL be applied to login (bcrypt comparison on non-existent emails). |
| NFR-14 | Login rate limiting SHALL block after 10 failures per email in 15 minutes. |
| NFR-15 | File uploads SHALL reject path traversal patterns and unsafe filenames. |
| NFR-16 | CORS SHALL restrict requests to configured PWA origins only. |
| NFR-17 | All inputs SHALL be validated server-side via Pydantic models with field constraints. |
| NFR-18 | The global exception handler SHALL return generic errors without exposing internals. |
| NFR-19 | All endpoints (except register, login, health) SHALL require a valid JWT Bearer token. |
| NFR-20 | The RAG assistant SHALL reject prompt injection attempts via scope keyword filtering. |

---

## 4. Usability

| ID | Requirement |
|----|-------------|
| NFR-21 | The application SHALL use a CSS custom property (token) system for consistent theming. |
| NFR-22 | Dark/light mode SHALL be toggleable and persisted in localStorage. |
| NFR-23 | The sidebar SHALL be always visible on desktop and collapse to hamburger on mobile. |
| NFR-24 | All interactive elements SHALL be keyboard-navigable; mobile drawer SHALL implement focus trap. |
| NFR-25 | Error messages SHALL be user-friendly and actionable; loading states SHALL show skeletons. |
| NFR-26 | All destructive actions SHALL require a confirmation step. |
| NFR-27 | Form inputs SHALL provide real-time validation and boundary enforcement. |
| NFR-28 | Currency formatting SHALL use the Philippine peso symbol (₱) with comma-separated thousands. |

---

## 5. Reliability & Availability

| ID | Requirement |
|----|-------------|
| NFR-29 | The PWA SHALL operate offline for cached pages and previously loaded forecast data. |
| NFR-30 | An offline banner SHALL appear when network connectivity is lost. |
| NFR-31 | The system SHALL gracefully degrade when Ollama is not running (all features except chat remain functional). |
| NFR-32 | The system SHALL fall back to cached/default values when external APIs are unavailable. |
| NFR-33 | The model artefact SHALL be backed up before training and restored if training fails. |
| NFR-34 | The health endpoint SHALL report subsystem status individually for partial degradation. |
| NFR-35 | Database operations SHALL use WAL mode for concurrent read performance. |

---

## 6. Maintainability

| ID | Requirement |
|----|-------------|
| NFR-36 | The backend SHALL follow modular architecture: `api/`, `model/`, `pipeline/`, `rag/`, `storage/`, `scraper/`. |
| NFR-37 | The frontend SHALL use page-based routing with shared context providers (Theme, Forecast, Auth). |
| NFR-38 | TypeScript strict typing SHALL be used; all API shapes SHALL have corresponding interfaces. |
| NFR-39 | Pydantic models SHALL validate all request/response schemas. |
| NFR-40 | Database migrations SHALL be idempotent (safe to run multiple times). |
| NFR-41 | All modules SHALL use Python standard logging with appropriate levels. |
| NFR-42 | CSS SHALL use custom properties exclusively — no hardcoded color values. |

---

## 7. Portability & Compatibility

| ID | Requirement |
|----|-------------|
| NFR-43 | The application SHALL run on Windows, macOS, and Linux without modification. |
| NFR-44 | Python 3.10+ and Node.js 18+ SHALL be the minimum runtime requirements. |
| NFR-45 | The application SHALL function in Chrome, Firefox, Edge, and Safari (latest two versions). |
| NFR-46 | The application SHALL be installable as a PWA on desktop and mobile. |
| NFR-47 | The application SHALL be accessible from LAN devices when configured with host 0.0.0.0. |
| NFR-48 | Core functionality (forecasting, entry, training) SHALL NOT require internet when data is cached. |

---

## 8. Data Integrity

| ID | Requirement |
|----|-------------|
| NFR-49 | SQLite SHALL enforce foreign key constraints between users and dependent tables. |
| NFR-50 | The year_month column SHALL prevent duplicate months per user. |
| NFR-51 | All timestamps SHALL be stored in ISO 8601 UTC format. |
| NFR-52 | CHECK constraints SHALL enforce valid ranges on chat text length, source type, and role values. |
| NFR-53 | saved_forecasts SHALL enforce one active forecast per user (UNIQUE on user_id). |
| NFR-54 | Model artefacts SHALL be serialized via joblib for efficient numpy/statsmodels persistence. |

---

## 9. Testability

| ID | Requirement |
|----|-------------|
| NFR-55 | An in-memory database factory SHALL be available for unit test isolation. |
| NFR-56 | Frontend components SHALL be testable with vitest + happy-dom; property-based tests via fast-check. |
| NFR-57 | A synthetic dataset generator SHALL produce realistic 48-month test data. |
| NFR-58 | Selenium automation SHALL support headless execution with HTML report generation. |

---

## 10. Deployment & Configuration

| ID | Requirement |
|----|-------------|
| NFR-59 | The application SHALL be deployable with two commands: `uvicorn` (backend) and `npm run dev` (frontend). |
| NFR-60 | Sensitive configuration SHALL be managed via .env (with .env.example documenting all variables). |
| NFR-61 | The production build SHALL use Vite with tree-shaking and minification. |
| NFR-62 | The application SHALL NOT require Docker, cloud hosting, or paid external services. |

---

## 11. Accessibility

| ID | Requirement |
|----|-------------|
| NFR-63 | Interactive elements SHALL have accessible labels or aria-label attributes. |
| NFR-64 | Decorative elements SHALL use aria-hidden="true". |
| NFR-65 | Focus SHALL be managed programmatically for drawers/modals (move in, restore on close). |
| NFR-66 | Color contrast SHALL meet WCAG 2.1 Level AA (4.5:1 normal text, 3:1 large text). |
| NFR-67 | The application SHALL be fully operable via keyboard alone. |
