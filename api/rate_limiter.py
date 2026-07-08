"""
In-memory login rate limiter for WATT-IF.

Tracks failed login attempts per email address using a simple dictionary.
Limits: 10 failed attempts per email within a 15-minute sliding window.

Requirements: 3.7
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, status


class LoginRateLimiter:
    """In-memory rate limiter: max 10 failed attempts per email per 15-minute window."""

    MAX_ATTEMPTS = 10
    WINDOW_SECONDS = 15 * 60  # 15 minutes

    def __init__(self) -> None:
        # email -> list of failure timestamps
        self._failures: dict[str, list[float]] = defaultdict(list)

    def _prune(self, email: str) -> None:
        """Remove entries older than the window."""
        cutoff = time.time() - self.WINDOW_SECONDS
        self._failures[email] = [
            t for t in self._failures[email] if t > cutoff
        ]

    def check(self, email: str) -> None:
        """Raise HTTPException(429) if the email has exceeded the attempt limit."""
        self._prune(email)
        if len(self._failures[email]) >= self.MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Try again later.",
            )

    def record_failure(self, email: str) -> None:
        """Record a failed login attempt for the given email."""
        self._failures[email].append(time.time())

    def reset(self, email: str) -> None:
        """Clear failure history for an email (called on successful login)."""
        self._failures.pop(email, None)


# Module-level singleton used by the auth router.
login_rate_limiter = LoginRateLimiter()
