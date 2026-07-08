# Implementation Plan: Account System

## Overview

This plan implements JWT-based authentication, per-user data isolation, and frontend auth flows for the WATT-IF application. The implementation follows a bottom-up approach: database schema first, then backend auth infrastructure, then per-user scoping of existing endpoints, then frontend auth context and UI pages, and finally test documentation updates.

## Tasks

- [x] 1. Database schema migration and default account seeding
  - [x] 1.1 Extend `storage/db.py` with users table and migration logic
    - Add `CREATE TABLE IF NOT EXISTS users` DDL (id, email, password_hash, created_at)
    - Add idempotent `ALTER TABLE ... ADD COLUMN user_id INTEGER REFERENCES users(id)` for monthly_bill_records, data_entry_log, chat_history, and training_log
    - Seed the default account (wattif@gmail.com / bcrypt-hashed "wattif", cost factor 12) if not already present
    - Assign orphaned rows (NULL user_id) to the default account's id
    - Ensure migrations are idempotent — running multiple times produces no errors or duplicate changes
    - Add startup check: if migration fails, log the error and prevent the app from serving requests
    - _Requirements: 1.1, 1.4, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ]* 1.2 Write property tests for migration idempotency and orphaned data assignment
    - **Property 10: Migration idempotency** — run migration N times on same DB, verify schema and data unchanged after first run
    - **Property 11: Orphaned data migration** — insert rows with NULL user_id, run migration, verify all assigned to default account
    - **Validates: Requirements 12.4, 12.5, 1.4**

- [x] 2. Backend auth infrastructure
  - [x] 2.1 Create `api/rate_limiter.py` with LoginRateLimiter class
    - Implement in-memory dict tracking failed login attempts per email with timestamps
    - `check(email)` raises HTTPException(429) if 10+ failures within 15-minute window
    - `record_failure(email)` records a failed attempt with current timestamp
    - `reset(email)` clears failure history on successful login
    - _Requirements: 3.7_

  - [x] 2.2 Create `api/dependencies.py` with JWT validation and get_current_user dependency
    - Use `python-jose` (or `PyJWT`) for JWT encoding/decoding with HS256
    - Read JWT_SECRET from environment variable (add to .env.example)
    - `get_current_user` extracts Bearer token from Authorization header, decodes, validates exp/sub/signature
    - Returns user dict `{"id": int, "email": str}` or raises HTTP 401
    - Verify the user ID in the token actually exists in the users table
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 2.3 Create `api/auth.py` with registration, login, and password-change endpoints
    - `POST /auth/register`: validate email format (one "@", domain with ".", ≤254 chars), password ≥8 chars, check duplicate, hash with bcrypt cost 12, create user, return 201
    - `POST /auth/login`: verify credentials, check rate limiter, issue JWT with sub/email/exp(24h)/iat, return token + email
    - `POST /auth/change-password`: require current_user dependency, verify current password, validate new password ≥8 chars and matches confirm, update hash
    - Run dummy bcrypt check on non-existent emails to prevent timing attacks
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 11.5, 11.6, 11.7, 11.8_

  - [x] 2.4 Register auth router in `api/main.py`
    - Import and include the auth router from `api/auth.py`
    - Add `JWT_SECRET` to `.env.example`
    - Add `bcrypt` and `python-jose[cryptography]` (or `PyJWT`) to project dependencies
    - _Requirements: 2.1, 3.1_

  - [ ]* 2.5 Write property tests for auth endpoints (backend, hypothesis + pytest)
    - **Property 1: Registration email/password validation** — generate invalid emails and short passwords, verify 422
    - **Property 2: Duplicate email rejection** — register, re-register same email, verify 409
    - **Property 3: Password hashing strength** — register random users, inspect bcrypt cost ≥12
    - **Property 4: JWT token structure** — login, decode token, verify sub/email/exp fields
    - **Property 5: Invalid credentials yield identical rejection** — wrong email/password both return same 401 message
    - **Property 6: Login rate limiting** — 10+ failures → 429
    - **Property 12: Password change validation** — test all valid/invalid combinations
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.7, 3.1, 3.2, 3.3, 3.4, 3.7, 11.5, 11.6, 11.7, 11.8**

- [x] 3. Checkpoint - Verify auth infrastructure
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Per-user data isolation on existing endpoints
  - [x] 4.1 Add `get_current_user` dependency to data-entry endpoints and filter by user_id
    - Modify `GET /data-entries` to filter by `user_id = current_user["id"]`
    - Modify `POST /data-entries` to set `user_id` on insert
    - Modify `PUT /data-entries/{id}` to verify ownership (403 if mismatch, 404 if not found)
    - Modify `DELETE /data-entries/{id}` to verify ownership (403 if mismatch, 404 if not found)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [x] 4.2 Add `get_current_user` dependency to upload, forecast, retrain, and model-info endpoints
    - Modify `POST /upload` to set `user_id` on all inserted/upserted records
    - Modify `POST /forecast` to load model from `data/models/{user_id}/sarimax_model.joblib`; return 503 if absent
    - Modify `POST /retrain` to train only on user's records and save to user's model path
    - Modify `GET /model-info` to load from user's model path
    - Create user model directory on first training: `data/models/{user_id}/`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [x] 4.3 Add `get_current_user` dependency to chat-history endpoints and filter by user_id
    - Modify `GET /chat-history` to filter by user_id, limit 100, order by created_at ASC
    - Modify `POST /chat-history` to set user_id on insert
    - Modify `DELETE /chat-history` to delete only user's records, return 204
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 4.4 Add `get_current_user` dependency to `DELETE /data/all` and scope deletion
    - Delete only the current user's records in monthly_bill_records, data_entry_log, training_log, chat_history
    - Delete the user's model artefact and directory (`data/models/{user_id}/`)
    - _Requirements: 7.5_

  - [ ]* 4.5 Write property tests for per-user data isolation (backend, hypothesis + pytest)
    - **Property 7: Token validation on protected endpoints** — invalid/expired/malformed tokens → 401
    - **Property 8: Per-user data isolation** — two users, each sees only their own data
    - **Property 9: Cross-user mutation rejection** — user A cannot edit/delete user B's entries → 403
    - **Validates: Requirements 5.1–5.6, 6.1–6.7, 8.1–8.5**

- [x] 5. Checkpoint - Verify backend isolation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Frontend auth context and API client updates
  - [x] 6.1 Create `frontend/src/context/AuthContext.tsx`
    - Implement AuthContextValue: user, token, login, register, logout, isLoading
    - On mount: check localStorage "wattif_token", decode JWT payload to get email/id, verify exp not passed
    - If token expired/invalid: clear localStorage, set user to null
    - login(): call POST /auth/login, store token in localStorage, set user state
    - register(): call POST /auth/register, then auto-login
    - logout(): clear localStorage "wattif_token", set user to null
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 9.7, 10.5_

  - [x] 6.2 Update `frontend/src/api/client.ts` to attach Bearer token and handle 401
    - Modify `request()` to read token from localStorage and set `Authorization: Bearer {token}` header
    - On 401 response: clear localStorage token, redirect to `/login`
    - _Requirements: 4.5, 4.6_

  - [x] 6.3 Create `frontend/src/components/AuthGuard.tsx`
    - Wrap protected routes; if no valid token, redirect to `/login`
    - Show loading spinner while `isLoading` is true in AuthContext
    - If authenticated user visits `/login` or `/register`, redirect to `/`
    - _Requirements: 9.1, 9.9_

- [x] 7. Frontend auth pages
  - [x] 7.1 Create `frontend/src/pages/LoginPage.tsx`
    - Labelled email input, labelled password input (masked), submit button
    - Link to Registration page
    - Generic "Invalid credentials" error on failure (no field-specific hints)
    - On success: redirect to Dashboard
    - _Requirements: 9.2, 9.3, 9.4, 9.5_

  - [x] 7.2 Create `frontend/src/pages/RegisterPage.tsx`
    - Labelled email, password, confirm-password inputs with submit button
    - Submit disabled until password ≥8 chars AND password === confirm-password
    - On success: auto-login and redirect to Dashboard
    - On failure: display error message indicating reason (duplicate email, validation)
    - _Requirements: 9.6, 9.7, 9.8_

  - [x] 7.3 Create `frontend/src/pages/AccountSettingsPage.tsx`
    - Display user email as read-only text
    - Password change form: current password, new password, confirm new password
    - Validate new password ≥8 chars and matches confirm; show inline errors
    - On success: show success message that persists until dismissed or navigated away
    - On incorrect current password: show error
    - Include logout button that clears session and redirects to Login
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9_

  - [ ]* 7.4 Write property tests for registration form and email truncation (frontend, fast-check + vitest)
    - **Property 13: Email display truncation** — random-length emails, verify truncation at 24 chars + ellipsis
    - **Property 14: Registration form submit-button state** — random password/confirm pairs, verify disabled/enabled logic
    - **Validates: Requirements 10.1, 9.6**

- [x] 8. Frontend routing, Sidebar, and TopBar integration
  - [x] 8.1 Update `frontend/src/App.tsx` routing with AuthGuard, login, register, and account routes
    - Wrap existing routes with AuthGuard
    - Add `/login` route → LoginPage (outside AuthGuard)
    - Add `/register` route → RegisterPage (outside AuthGuard)
    - Add `/account` route → AccountSettingsPage (inside AuthGuard)
    - Wrap entire app with AuthContext provider
    - _Requirements: 9.1, 9.9, 11.2_

  - [x] 8.2 Update `frontend/src/components/Sidebar.tsx` with user email display and logout button
    - Display authenticated user's email in Sidebar bottom section
    - Truncate email with ellipsis if >24 characters
    - Add "Logout" button below email display
    - On logout: clear token, redirect to Login within 1 second
    - Handle network errors during logout gracefully (still clear local token)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 8.3 Update `frontend/src/components/TopBar.tsx` with Account icon linking to settings
    - Display Account icon in upper-right area
    - On click: navigate to `/account` (Account Settings Page)
    - _Requirements: 11.1, 11.2_

- [x] 9. Default account auto-login logic
  - [~] 9.1 Implement default account auto-login in AuthContext
    - On startup: if no stored token AND only default account exists (check via an endpoint or token presence heuristic), auto-login with default credentials
    - If additional user accounts exist: do NOT auto-login, show Login page
    - Add backend endpoint `GET /auth/has-users` returning `{"has_other_users": bool}` to check if accounts beyond default exist
    - _Requirements: 1.2, 1.3, 1.5, 1.6_

- [x] 10. Checkpoint - Verify full integration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Test documentation updates
  - [x] 11.1 Update `Documentation/Test_Plan.md` with account system test items
    - Add account system components to Section 2 (Test Items): registration form, login form, logout action, session persistence mechanism, data isolation behavior
    - Add "Account System" subsection to Section 3 (Features to Be Tested): registration, login, logout, session persistence, data isolation, error handling
    - Add row to Section 6 (Item Pass/Fail Criteria) for account/authentication features defining pass and fail conditions
    - _Requirements: 13.1, 13.4_

  - [x] 11.2 Create `Documentation/TC_ACT_AccountSystem.md` test case document
    - Use ACT prefix for all test case IDs (ACT-01, ACT-02, etc.)
    - Include at least 1 test case per category: registration, login, logout, session persistence, data isolation, error handling (minimum 6 total)
    - Each test case includes: ID, Summary, Pre-condition, Test Steps (numbered), Expected Result, Actual Result (blank), Status (⬜ Not Run), Notes
    - _Requirements: 13.2, 13.3_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Backend uses Python (FastAPI + pytest + hypothesis); frontend uses TypeScript (React + vitest + fast-check)
- The JWT_SECRET environment variable must be added to `.env` and `.env.example` before auth endpoints function

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1", "2.2"] },
    { "id": 2, "tasks": ["2.3", "6.1"] },
    { "id": 3, "tasks": ["2.4", "2.5", "6.2"] },
    { "id": 4, "tasks": ["4.1", "4.2", "4.3", "4.4", "6.3"] },
    { "id": 5, "tasks": ["4.5", "7.1", "7.2", "7.3"] },
    { "id": 6, "tasks": ["7.4", "8.1"] },
    { "id": 7, "tasks": ["8.2", "8.3", "9.1"] },
    { "id": 8, "tasks": ["11.1", "11.2"] }
  ]
}
```
