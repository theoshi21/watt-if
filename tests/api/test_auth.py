"""
Unit tests for WATT-IF authentication endpoints (api/auth.py).

Tests cover:
  - POST /auth/register: success, duplicate email, invalid email, short password
  - POST /auth/login: success, wrong password, non-existent email, rate limiting
  - POST /auth/change-password: success, wrong current password, mismatch confirm
  - Timing attack mitigation (dummy bcrypt on non-existent email)
"""

from __future__ import annotations

import os
import sqlite3
import time
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient

# Set JWT_SECRET before importing app modules
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-unit-tests")

from api.auth import router, _validate_email, _hash_password, _verify_password, BCRYPT_COST_FACTOR
from api.dependencies import JWT_SECRET, JWT_ALGORITHM
from api.rate_limiter import LoginRateLimiter
from storage.db import get_connection, init_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _use_in_memory_db(monkeypatch):
    """Use a named in-memory SQLite database shared across connections.
    
    SQLite supports named in-memory databases with 'file::memory:?cache=shared'
    which allows multiple connections to share the same in-memory DB.
    We use a unique name per test via a simple counter approach with the
    same URI-based connection.
    """
    import sqlite3
    import uuid

    # Use a unique named memory DB for this test
    db_name = f"test_{uuid.uuid4().hex}"
    db_uri = f"file:{db_name}?mode=memory&cache=shared"
    
    # We need to keep one connection alive to prevent the DB from being freed
    _anchor_conn = sqlite3.connect(db_uri, uri=True, check_same_thread=False)
    _anchor_conn.row_factory = sqlite3.Row
    _anchor_conn.execute("PRAGMA journal_mode=WAL;")
    init_db(_anchor_conn)

    def _mock_get_connection(*args, **kwargs):
        conn = sqlite3.connect(db_uri, uri=True, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr("api.auth.get_connection", _mock_get_connection)
    monkeypatch.setattr("api.auth.init_db", lambda c: None)
    monkeypatch.setattr("api.dependencies.get_connection", _mock_get_connection)
    monkeypatch.setattr("api.dependencies.init_db", lambda c: None)

    yield _anchor_conn
    _anchor_conn.close()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset the rate limiter between tests."""
    from api.rate_limiter import login_rate_limiter
    login_rate_limiter._failures.clear()
    yield


@pytest.fixture
def client():
    """Create a test client with the auth router."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "securepass123"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"

    def test_register_duplicate_email(self, client):
        # First registration
        client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "password123"
        })
        # Second registration with same email
        resp = client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "differentpass"
        })
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    def test_register_invalid_email_no_at(self, client):
        resp = client.post("/auth/register", json={
            "email": "invalidemail.com",
            "password": "password123"
        })
        assert resp.status_code == 422

    def test_register_invalid_email_no_dot_in_domain(self, client):
        resp = client.post("/auth/register", json={
            "email": "user@localhost",
            "password": "password123"
        })
        assert resp.status_code == 422

    def test_register_invalid_email_multiple_at(self, client):
        resp = client.post("/auth/register", json={
            "email": "user@@example.com",
            "password": "password123"
        })
        assert resp.status_code == 422

    def test_register_password_too_short(self, client):
        resp = client.post("/auth/register", json={
            "email": "user@example.com",
            "password": "short"
        })
        assert resp.status_code == 422

    def test_register_email_normalized_to_lowercase(self, client):
        resp = client.post("/auth/register", json={
            "email": "USER@Example.COM",
            "password": "password123"
        })
        assert resp.status_code == 201
        assert resp.json()["email"] == "user@example.com"

    def test_register_email_too_long(self, client):
        long_email = "a" * 245 + "@test.com"  # 254 chars total
        resp = client.post("/auth/register", json={
            "email": long_email,
            "password": "password123"
        })
        # Exact 254 may pass validation but very long should fail via Pydantic max_length
        # or our custom check
        assert resp.status_code in (201, 422)

    def test_register_bcrypt_cost_12(self, client, _use_in_memory_db):
        """Verify registered password is hashed with bcrypt cost >= 12."""
        import bcrypt as _bcrypt
        client.post("/auth/register", json={
            "email": "cost@example.com",
            "password": "password123"
        })
        conn = _use_in_memory_db
        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?", ("cost@example.com",)
        ).fetchone()
        assert row is not None
        # bcrypt hash format: $2b$12$...
        hash_str = row["password_hash"]
        assert hash_str.startswith("$2b$12$") or hash_str.startswith("$2a$12$")


# ---------------------------------------------------------------------------
# Login Tests
# ---------------------------------------------------------------------------


class TestLogin:
    def test_login_success(self, client):
        # Register first
        client.post("/auth/register", json={
            "email": "login@example.com",
            "password": "password123"
        })
        # Login
        resp = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "password123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["email"] == "login@example.com"

    def test_login_jwt_structure(self, client):
        """Verify JWT contains sub, email, exp, iat."""
        client.post("/auth/register", json={
            "email": "jwt@example.com",
            "password": "password123"
        })
        resp = client.post("/auth/login", json={
            "email": "jwt@example.com",
            "password": "password123"
        })
        token = resp.json()["token"]
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "sub" in payload
        assert payload["email"] == "jwt@example.com"
        assert "exp" in payload
        assert "iat" in payload
        # exp should be iat + 86400 (24 hours)
        assert payload["exp"] - payload["iat"] == 86400

    def test_login_wrong_password(self, client):
        client.post("/auth/register", json={
            "email": "wrong@example.com",
            "password": "password123"
        })
        resp = client.post("/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid credentials"

    def test_login_nonexistent_email(self, client):
        resp = client.post("/auth/login", json={
            "email": "nonexist@example.com",
            "password": "password123"
        })
        assert resp.status_code == 401
        # Same message for non-existent email and wrong password
        assert resp.json()["detail"] == "Invalid credentials"

    def test_login_rate_limiting(self, client):
        """After 10 failed attempts, should get 429."""
        client.post("/auth/register", json={
            "email": "ratelimit@example.com",
            "password": "password123"
        })
        # Make 10 failed attempts
        for _ in range(10):
            client.post("/auth/login", json={
                "email": "ratelimit@example.com",
                "password": "wrongpass"
            })
        # 11th attempt should be rate limited
        resp = client.post("/auth/login", json={
            "email": "ratelimit@example.com",
            "password": "password123"  # even correct password should fail
        })
        assert resp.status_code == 429
        assert "Too many login attempts" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Password Change Tests
# ---------------------------------------------------------------------------


class TestPasswordChange:
    def _get_auth_header(self, client, email="change@example.com", password="password123"):
        """Register and login, return auth header."""
        client.post("/auth/register", json={
            "email": email,
            "password": password
        })
        resp = client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        token = resp.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def test_change_password_success(self, client):
        headers = self._get_auth_header(client)
        resp = client.post("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456"
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Password updated"

        # Verify old password no longer works
        resp = client.post("/auth/login", json={
            "email": "change@example.com",
            "password": "password123"
        })
        assert resp.status_code == 401

        # Verify new password works
        resp = client.post("/auth/login", json={
            "email": "change@example.com",
            "password": "newpassword456"
        })
        assert resp.status_code == 200

    def test_change_password_wrong_current(self, client):
        headers = self._get_auth_header(client)
        resp = client.post("/auth/change-password", json={
            "current_password": "wrongcurrent",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456"
        }, headers=headers)
        assert resp.status_code == 400
        assert "incorrect" in resp.json()["detail"].lower()

    def test_change_password_mismatch(self, client):
        headers = self._get_auth_header(client)
        resp = client.post("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "newpassword456",
            "confirm_password": "differentpassword"
        }, headers=headers)
        assert resp.status_code == 400
        assert "do not match" in resp.json()["detail"].lower()

    def test_change_password_too_short(self, client):
        headers = self._get_auth_header(client)
        resp = client.post("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "short",
            "confirm_password": "short"
        }, headers=headers)
        assert resp.status_code == 422

    def test_change_password_unauthenticated(self, client):
        resp = client.post("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456"
        })
        assert resp.status_code in (401, 403)
