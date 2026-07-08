"""
Authentication endpoints for WATT-IF.

Provides:
  POST /auth/register       — create a new user account
  POST /auth/login          — authenticate and receive a JWT
  POST /auth/change-password — update the current user's password

Requirements: 2.1–2.7, 3.1–3.7, 11.5–11.8
"""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import datetime, timezone

import bcrypt
import jwt  # PyJWT
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import JWT_ALGORITHM, JWT_SECRET, get_current_user
from api.rate_limiter import login_rate_limiter
from storage.db import DEFAULT_DB_PATH, get_connection, init_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BCRYPT_COST_FACTOR = 12
JWT_EXPIRY_SECONDS = 24 * 60 * 60  # 24 hours

# Dummy hash used for timing-attack mitigation on non-existent emails.
# Pre-computed bcrypt hash so the server still spends time on bcrypt.checkpw().
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password-for-timing", bcrypt.gensalt(rounds=BCRYPT_COST_FACTOR))


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_email(email: str) -> None:
    """Validate email format: one '@', non-empty local, domain with '.', ≤254 chars.

    Raises HTTPException(422) on invalid format.
    """
    if len(email) > 254:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email must not exceed 254 characters.",
        )

    # Must have exactly one "@"
    parts = email.split("@")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format.",
        )

    local_part, domain = parts

    # Local part must have at least one character
    if not local_part:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format.",
        )

    # Domain must have at least one "."
    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format.",
        )

    # Domain parts must not be empty (handles ".." cases)
    domain_parts = domain.split(".")
    if any(not part for part in domain_parts):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format.",
        )


def _hash_password(password: str) -> str:
    """Hash a password with bcrypt at cost factor 12."""
    salt = bcrypt.gensalt(rounds=BCRYPT_COST_FACTOR)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _create_jwt(user_id: int, email: str) -> str:
    """Create a JWT token with sub, email, exp (24h), and iat claims."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/has-users")
async def has_users() -> dict:
    """Check whether any user accounts exist beyond the default account.

    This endpoint is called before login to determine whether automatic
    login with the default account should be attempted.  It does NOT
    require authentication.

    Returns {"has_other_users": true} if additional user accounts exist,
    {"has_other_users": false} if only the default account is present.
    """
    conn = get_connection(DEFAULT_DB_PATH)
    try:
        init_db(conn)
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE email != ?",
            ("wattif@gmail.com",),
        ).fetchone()
        count = row["cnt"] if row else 0
    finally:
        conn.close()

    return {"has_other_users": count > 0}


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest) -> RegisterResponse:
    """Create a new user account.

    Validates email format and password length, checks for duplicate email,
    hashes the password with bcrypt cost 12, and creates the user record.
    """
    # Validate email format (beyond Pydantic max_length)
    _validate_email(request.email)

    # Normalize email to lowercase for consistent duplicate checking
    email = request.email.strip().lower()

    # Hash password
    password_hash = _hash_password(request.password)

    # Persist user
    conn = get_connection(DEFAULT_DB_PATH)
    try:
        init_db(conn)

        # Check for duplicate
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        created_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, password_hash, created_at),
        )
        conn.commit()
    finally:
        conn.close()

    return RegisterResponse(email=email)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """Authenticate a user and return a JWT token.

    Checks rate limiter, verifies credentials, issues a JWT.
    Runs a dummy bcrypt check on non-existent emails to prevent timing attacks.
    """
    email = request.email.strip().lower()

    # Check rate limiter first
    login_rate_limiter.check(email)

    conn = get_connection(DEFAULT_DB_PATH)
    try:
        init_db(conn)
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        # Run dummy bcrypt check to prevent timing attacks
        bcrypt.checkpw(b"dummy-password", _DUMMY_HASH)
        login_rate_limiter.record_failure(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Verify password
    if not _verify_password(request.password, row["password_hash"]):
        login_rate_limiter.record_failure(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Success — reset rate limiter and issue JWT
    login_rate_limiter.reset(email)
    token = _create_jwt(row["id"], row["email"])

    return LoginResponse(token=token, email=row["email"])


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Change the authenticated user's password.

    Verifies the current password, validates the new password meets
    requirements, and updates the stored hash.
    """
    # Validate new password matches confirmation
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match.",
        )

    # Fetch current hash
    conn = get_connection(DEFAULT_DB_PATH)
    try:
        init_db(conn)
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (current_user["id"],)
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        # Verify current password
        if not _verify_password(request.current_password, row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        # Update password hash
        new_hash = _hash_password(request.new_password)
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return {"message": "Password updated"}
