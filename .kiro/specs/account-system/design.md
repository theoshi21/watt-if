# Design Document: Account System

## Overview

This design introduces authentication, authorization, and per-user data isolation to the WATT-IF application. Currently, the app operates as a single-user system with a shared SQLite database and a single SARIMAX model artefact. The account system adds:

1. A `users` table and JWT-based authentication (registration, login, logout)
2. Per-user scoping of bill records, data entries, chat history, and model artefacts
3. A default account for seamless first-use experience
4. Frontend login/registration pages, route guards, and account settings
5. Database migration that preserves existing data by assigning it to the default account

The system prioritizes simplicity — no external auth providers, no refresh tokens in the initial version — while maintaining security through bcrypt hashing, short-lived JWTs, and rate limiting.

## Architecture

```mermaid
graph TD
    subgraph Frontend [React Frontend]
        LP[Login Page]
        RP[Registration Page]
        ASP[Account Settings Page]
        AG[AuthGuard Component]
        AC[AuthContext Provider]
        AP[API Client with Auth Header]
    end

    subgraph Backend [FastAPI Backend]
        AR[Auth Router<br>/auth/register, /auth/login]
        AM[Auth Middleware<br>JWT Validation]
        GCD[get_current_user Dependency]
        EP[Existing Endpoints<br>/upload, /forecast, /ask, etc.]
        DB[(SQLite Database)]
        FS[Filesystem<br>data/models/{user_id}/]
    end

    LP --> AP
    RP --> AP
    ASP --> AP
    AG --> AC
    AC --> AP
    AP -->|Authorization: Bearer token| AR
    AP -->|Authorization: Bearer token| EP
    AR --> DB
    AM --> GCD
    GCD --> EP
    EP --> DB
    EP --> FS
```

### Key Architectural Decisions

1. **JWT stored in localStorage**: Simpler than httpOnly cookies for this single-origin SPA. The JWT contains the user ID and email, with a 24-hour expiry. No refresh token mechanism in v1.

2. **FastAPI Dependency Injection for auth**: A `get_current_user` dependency extracts and validates the JWT from the Authorization header, returning the user record. All protected endpoints declare this dependency.

3. **SQLite schema migration at startup**: The existing `init_db()` function is extended with idempotent ALTER TABLE statements to add `user_id` columns. A migration step assigns orphaned rows to the default account.

4. **Per-user model artefact paths**: Model files move from `data/sarimax_model.joblib` to `data/models/{user_id}/sarimax_model.joblib`. The `SARIMAXModel` class accepts a path parameter already, so this is a configuration change.

5. **Rate limiting via in-memory dict**: For login attempts, a simple dictionary tracks failed attempts per email with timestamps. This is adequate for a single-process deployment. No external Redis needed.

## Components and Interfaces

### Backend Components

#### 1. Auth Module (`api/auth.py`)

```python
# New file: api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=8)

class RegisterResponse(BaseModel):
    email: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    email: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

# Endpoints:
# POST /auth/register -> RegisterResponse (201)
# POST /auth/login -> LoginResponse (200)
# POST /auth/change-password -> {"message": "Password updated"} (200)
```

#### 2. Auth Dependencies (`api/dependencies.py`)

```python
# New file: api/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate JWT and return user dict with 'id' and 'email'.
    
    Raises HTTP 401 if token is missing, expired, malformed,
    or references a non-existent user.
    """
    ...
```

#### 3. Rate Limiter (`api/rate_limiter.py`)

```python
# New file: api/rate_limiter.py

class LoginRateLimiter:
    """In-memory rate limiter: max 10 failed attempts per email per 15-minute window."""
    
    def check(self, email: str) -> None:
        """Raises HTTPException(429) if limit exceeded."""
        ...
    
    def record_failure(self, email: str) -> None:
        """Record a failed login attempt."""
        ...
    
    def reset(self, email: str) -> None:
        """Clear failures for an email (called on successful login)."""
        ...
```

#### 4. Database Migration Extension (`storage/db.py`)

The existing `init_db()` is extended with:
- `CREATE TABLE IF NOT EXISTS users` DDL
- Idempotent `ALTER TABLE ... ADD COLUMN user_id` for existing tables
- Default account seeding
- Orphaned row migration

#### 5. Modified Existing Endpoints

All data endpoints (`/upload`, `/forecast`, `/data-entries`, `/chat-history`, `/retrain`, `/data/all`) gain a `current_user = Depends(get_current_user)` parameter and filter queries by `current_user["id"]`.

### Frontend Components

#### 1. AuthContext (`frontend/src/context/AuthContext.tsx`)

```typescript
interface AuthContextValue {
  user: { email: string; id: number } | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean  // true during initial token validation
}
```

#### 2. AuthGuard (`frontend/src/components/AuthGuard.tsx`)

Wraps protected routes. Checks for a valid (non-expired) token in localStorage. Redirects to `/login` if absent or expired.

#### 3. Login Page (`frontend/src/pages/LoginPage.tsx`)

Email + password form. Generic error message on failure. Link to registration.

#### 4. Registration Page (`frontend/src/pages/RegisterPage.tsx`)

Email + password + confirm password form. Submit disabled until validation passes. Auto-login on success.

#### 5. Account Settings Page (`frontend/src/pages/AccountSettingsPage.tsx`)

Displays email (read-only), password change form, logout button.

#### 6. Updated API Client (`frontend/src/api/client.ts`)

The existing `request()` helper is modified to attach the Bearer token from localStorage to every request. On 401 responses, it clears the token and redirects to login.

#### 7. Updated Sidebar

Bottom section gains user email display (truncated at 24 chars) and a Logout button.

#### 8. Updated TopBar

The existing UserCircleIcon button becomes a link to `/account`.

## Data Models

### Database Schema Changes

```sql
-- New table
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE CHECK(length(email) <= 254),
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL  -- ISO 8601
);

-- Add user_id to existing tables (idempotent migration)
ALTER TABLE monthly_bill_records ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE data_entry_log ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE chat_history ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE training_log ADD COLUMN user_id INTEGER REFERENCES users(id);
```

### JWT Token Payload

```json
{
  "sub": 1,
  "email": "user@example.com",
  "exp": 1719532800,
  "iat": 1719446400
}
```

- `sub`: User ID (integer)
- `email`: User email (for frontend display without extra API call)
- `exp`: Expiration timestamp (24 hours from issuance)
- `iat`: Issued-at timestamp

### Model Artefact Path Convention

```
data/models/{user_id}/sarimax_model.joblib
```

Example: User ID 1 → `data/models/1/sarimax_model.joblib`

### Default Account

```
email: wattif@gmail.com
password: wattif (bcrypt hashed, cost factor 12)
id: 1 (first row in users table)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Registration email and password validation

*For any* string submitted as an email that does not contain exactly one "@" with at least one character before it and a domain with at least one "." after it, or exceeds 254 characters, the registration endpoint SHALL return HTTP 422. *For any* string submitted as a password with fewer than 8 characters, the registration endpoint SHALL return HTTP 422.

**Validates: Requirements 2.3, 2.4, 2.5**

### Property 2: Duplicate email rejection

*For any* email that already exists in the users table, submitting a registration request with that email SHALL return HTTP 409.

**Validates: Requirements 2.2**

### Property 3: Password hashing strength

*For any* successfully registered user, the stored `password_hash` in the database SHALL be a valid bcrypt hash with a cost factor of at least 12.

**Validates: Requirements 2.7**

### Property 4: JWT token structure

*For any* successful login, the returned JWT token SHALL contain a `sub` field matching the user's database ID, an `email` field matching the user's email, and an `exp` claim exactly 86400 seconds (24 hours) after the `iat` claim.

**Validates: Requirements 3.1, 3.4**

### Property 5: Invalid credentials yield identical rejection

*For any* login attempt where the email does not exist in the database OR the password does not match the stored hash, the login endpoint SHALL return HTTP 401 with the same generic error message, making it impossible to distinguish which field was wrong.

**Validates: Requirements 3.2, 3.3**

### Property 6: Login rate limiting

*For any* email address, after 10 failed login attempts within a 15-minute window, the next login attempt for that email SHALL return HTTP 429 regardless of whether the credentials are correct.

**Validates: Requirements 3.7**

### Property 7: Token validation on protected endpoints

*For any* request to a protected endpoint that is missing an Authorization header, or contains an expired JWT, or contains a malformed token, or contains a token with an invalid cryptographic signature, or contains a token referencing a non-existent user ID, the endpoint SHALL return HTTP 401 Unauthorized.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.6**

### Property 8: Per-user data isolation

*For any* two distinct authenticated users A and B, if user A creates bill records, data entries, or chat messages, then user B's queries for those same resource types SHALL never include user A's records. Each user's query SHALL return only records where `user_id` matches their own authenticated identity.

**Validates: Requirements 5.5, 6.1, 6.2, 6.7, 8.1, 8.2**

### Property 9: Cross-user mutation rejection

*For any* authenticated user A attempting to edit or delete a data entry or chat record belonging to a different user B, the system SHALL return HTTP 403 Forbidden and leave the record unchanged.

**Validates: Requirements 6.3, 6.4, 8.5**

### Property 10: Migration idempotency

*For any* database state, running the schema migration function N times (N ≥ 1) SHALL produce the same schema and data as running it once, with no errors on subsequent runs.

**Validates: Requirements 12.4**

### Property 11: Orphaned data migration

*For any* set of existing rows in monthly_bill_records, data_entry_log, chat_history, or training_log with NULL user_id, after migration completes, all such rows SHALL have their user_id set to the Default_Account's id, and no rows SHALL remain with NULL user_id.

**Validates: Requirements 1.4, 12.5**

### Property 12: Password change validation

*For any* password change request, the operation SHALL succeed if and only if: the current password matches the stored hash, the new password is at least 8 characters long, and the new password matches the confirm password field. Violation of any condition SHALL result in rejection with an appropriate error.

**Validates: Requirements 11.5, 11.6, 11.7, 11.8**

### Property 13: Email display truncation

*For any* email string of length greater than 24 characters, the displayed value in the Sidebar SHALL be truncated to 24 characters followed by an ellipsis ("…"). *For any* email string of length 24 or fewer characters, it SHALL be displayed in full without truncation.

**Validates: Requirements 10.1**

### Property 14: Registration form submit-button state

*For any* combination of password and confirm-password field values, the registration form submit button SHALL be disabled if the password is fewer than 8 characters OR the password and confirm-password values do not match. It SHALL be enabled only when both conditions are satisfied.

**Validates: Requirements 9.6**

## Error Handling

### Backend Errors

| Scenario | HTTP Status | Response Body | Behavior |
|----------|-------------|---------------|----------|
| Missing/invalid/expired JWT | 401 | `{"detail": "Not authenticated"}` | Request rejected before reaching endpoint logic |
| Non-existent user in valid JWT | 401 | `{"detail": "Not authenticated"}` | Same as above (no info leakage) |
| Login with wrong credentials | 401 | `{"detail": "Invalid credentials"}` | Same message for wrong email or wrong password |
| Rate limit exceeded | 429 | `{"detail": "Too many login attempts. Try again later."}` | 15-minute cooldown |
| Duplicate email registration | 409 | `{"detail": "Email already registered"}` | Clear message |
| Validation failure (email/password) | 422 | `{"detail": "...specific reason..."}` | FastAPI/Pydantic validation |
| Cross-user data access | 403 | `{"detail": "Access denied"}` | Logged as potential security event |
| Entry not found | 404 | `{"detail": "Entry not found"}` | Standard not-found |
| Model not trained (per-user) | 503 | `{"detail": "Model not trained. Please train your model first."}` | User-specific model missing |
| Migration failure at startup | — | App refuses to start | Logged; no requests served |

### Frontend Error Handling

| Scenario | Behavior |
|----------|----------|
| 401 on any API call | Clear localStorage token, redirect to `/login` |
| 403 on any API call | Display "Access denied" toast/banner |
| Network failure during logout | Still clear local token and redirect |
| Expired token detected on page load | Clear token, redirect to `/login` |
| Registration validation failure | Show inline error below the offending field |
| Login failure | Show generic "Invalid credentials" message |

### Security Considerations

- **Timing attacks**: bcrypt's fixed-cost comparison prevents timing-based password guessing. Login with non-existent email still runs a dummy bcrypt check to equalize response time.
- **JWT secret**: Stored in `.env` as `JWT_SECRET`. Generated randomly on first deploy. Never committed to version control.
- **Token in localStorage**: Acceptable for this single-origin SPA. XSS mitigation relies on React's built-in escaping and CSP headers.
- **Rate limiter state**: In-memory; resets on server restart. Acceptable for single-process deployment.

## Testing Strategy

### Unit Tests (Example-based)

Unit tests cover specific scenarios, edge cases, and UI rendering:

- **Auth endpoints**: Registration success, duplicate email, login success/failure, missing fields
- **Session management**: Token stored in localStorage, expired token handling, logout flow
- **Frontend pages**: LoginPage renders inputs, RegistrationPage disables button correctly, AccountSettings displays email
- **Migration**: Idempotent runs, orphaned data assigned to default account, existing data preserved
- **Default account**: Created on init, auto-login when sole account, disabled auto-login with multiple accounts

### Property-Based Tests

Property-based tests verify universal correctness properties across randomized inputs. The project already has `fast-check` (v3.23.2) installed for the frontend. For the Python backend, `hypothesis` will be used.

**Configuration**:
- Minimum 100 iterations per property test
- Each property test references its design document property via tag comment

**Backend property tests** (Python + Hypothesis):
- Property 1: Email/password validation — generate random invalid emails and short passwords, verify 422
- Property 2: Duplicate email — register, then re-register same email, verify 409
- Property 3: Bcrypt cost — register random users, inspect stored hash cost
- Property 4: JWT structure — login random users, decode and verify all claims
- Property 5: Invalid credentials — random wrong passwords/emails → uniform 401
- Property 6: Rate limiting — N failed attempts → 429 after threshold
- Property 7: Token validation — generate invalid tokens (expired, malformed, bad signature) → 401
- Property 8: Data isolation — create data for random users, cross-query returns empty
- Property 9: Cross-user mutation — attempt edit/delete across users → 403
- Property 10: Migration idempotency — run migration N times, verify consistent state
- Property 11: Orphaned migration — random orphaned rows → all get default user_id
- Property 12: Password change — valid/invalid combinations, verify correct accept/reject

**Frontend property tests** (TypeScript + fast-check):
- Property 13: Email truncation — generate random-length emails, verify truncation logic
- Property 14: Registration form — generate random password/confirm pairs, verify button state

**Tag format**: `Feature: account-system, Property {N}: {description}`

### Integration Tests

- End-to-end auth flow: register → login → access data → logout → verify access denied
- Multi-user scenario: two users upload different CSVs, each sees only their own data
- Model training isolation: two users train models, each forecast uses their own artefact
- Default account migration: pre-seed data without user_id, run app, verify assignment

### Test Libraries

| Layer | Library | Notes |
|-------|---------|-------|
| Backend unit/property | pytest + hypothesis | hypothesis for PBT |
| Backend integration | pytest + httpx (TestClient) | FastAPI TestClient |
| Frontend unit/property | vitest + fast-check | Already configured |
| Frontend component | @testing-library/react | Already installed |

