"""
Integration tests for WATT-IF API endpoints.

Covers:
  11.1 — POST /forecast with horizon=9 and horizon=12 returns the correct
          number of ForecastMonth objects
  11.2 — POST /data-entries then GET /data-entries round-trip returns the
          correct row in the list
  11.3 — POST /chat-history then GET /chat-history returns the correct
          message in the list

Tests run against FastAPI's TestClient without starting a live server.
All external I/O (SQLite file, SARIMAX model, VectorStore, Ollama) is
either patched or replaced with an in-memory SQLite database.

Requirements: 2.4, 4.2, 4.3, 5.2, 5.3
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from pipeline.models import ForecastMonth
from storage.db import create_in_memory_db

# ---------------------------------------------------------------------------
# Module-level TestClient
#
# Using a module-level TestClient (rather than one inside a ``with`` block)
# avoids triggering the ``@app.on_event("startup")`` Ollama warmup during
# test collection, which would block indefinitely when Ollama is not running.
# ---------------------------------------------------------------------------

client = TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# DB proxy helper
# ---------------------------------------------------------------------------


class _NoCloseConn:
    """Thin proxy around sqlite3.Connection that makes ``close()`` a no-op.

    Each API endpoint calls ``conn.close()`` in a ``finally`` block.  For an
    in-memory SQLite database this destroys the DB before the next request.
    This proxy intercepts ``close()`` so the shared in-memory DB stays alive
    for the full duration of a test, while all other attribute accesses fall
    through to the real connection.
    """

    def __init__(self, real_conn: sqlite3.Connection) -> None:
        self._real = real_conn

    def close(self) -> None:  # intentional no-op
        pass

    def __getattr__(self, name: str):
        return getattr(self._real, name)


# ---------------------------------------------------------------------------
# Per-test in-memory DB fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_proxy() -> _NoCloseConn:
    """Yield a ``_NoCloseConn`` proxy over a fresh in-memory SQLite DB."""
    real_conn = create_in_memory_db()
    proxy = _NoCloseConn(real_conn)
    yield proxy
    real_conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_forecast_months(n: int) -> list[ForecastMonth]:
    """Build a list of *n* minimal ForecastMonth objects for mocking."""
    return [
        ForecastMonth(
            year_month=f"2025-{(i % 12) + 1:02d}",
            kwh_forecast=300.0,
            kwh_lower_95=280.0,
            kwh_upper_95=320.0,
            price_forecast=60.0,
            price_lower_95=56.0,
            price_upper_95=64.0,
            meralco_rate=11.8,
            avg_temperature=28.5,
            avg_humidity=78.0,
            total_rainfall_mm=150.0,
            holiday_count=2,
            weekend_count=8,
            hot_days_count=10,
            rainy_days_count=8,
            is_el_nino=0,
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# 11.1  Extended horizons
# ---------------------------------------------------------------------------


class TestForecastHorizons:
    """Integration tests for extended forecast horizons (Requirements 2.4)."""

    def _post_forecast(self, horizon: int) -> dict:
        """POST /forecast with a mocked SARIMAXModel that returns *horizon* months."""
        mock_model = MagicMock()
        mock_model.forecast.return_value = _make_forecast_months(horizon)

        with patch("api.main.SARIMAXModel", return_value=mock_model), \
             patch("api.main.VectorStore") as mock_vs_cls:
            mock_vs_cls.return_value.upsert.return_value = None
            resp = client.post("/forecast", json={"horizon": horizon})

        assert resp.status_code == 200, resp.text
        return resp.json()

    def test_horizon_9_returns_9_forecast_months(self) -> None:
        """POST /forecast with horizon=9 SHALL return exactly 9 ForecastMonth objects.

        Requirements: 2.4
        """
        data = self._post_forecast(horizon=9)

        assert data["horizon"] == 9
        months = data["months"]
        assert isinstance(months, list)
        assert len(months) == 9, (
            f"Expected 9 ForecastMonth objects in response, got {len(months)}"
        )

    def test_horizon_12_returns_12_forecast_months(self) -> None:
        """POST /forecast with horizon=12 SHALL return exactly 12 ForecastMonth objects.

        Requirements: 2.4
        """
        data = self._post_forecast(horizon=12)

        assert data["horizon"] == 12
        months = data["months"]
        assert isinstance(months, list)
        assert len(months) == 12, (
            f"Expected 12 ForecastMonth objects in response, got {len(months)}"
        )

    def test_invalid_horizon_returns_422(self) -> None:
        """POST /forecast with an unsupported horizon SHALL return HTTP 422.

        Validates the Pydantic schema validator is in effect.
        Requirements: 2.5
        """
        resp = client.post("/forecast", json={"horizon": 7})
        assert resp.status_code == 422

    def test_forecast_month_fields_present(self) -> None:
        """Each returned ForecastMonth SHALL contain the required fields.

        Requirements: 2.4
        """
        data = self._post_forecast(horizon=9)
        required_fields = {
            "year_month",
            "kwh_forecast",
            "kwh_lower_95",
            "kwh_upper_95",
            "price_forecast",
            "price_lower_95",
            "price_upper_95",
        }
        for month in data["months"]:
            missing = required_fields - set(month.keys())
            assert not missing, f"ForecastMonth missing fields: {missing}"


# ---------------------------------------------------------------------------
# 11.2  Data entry persistence
# ---------------------------------------------------------------------------


class TestDataEntryPersistence:
    """Integration tests for POST → GET /data-entries round-trip (Requirements 4.3)."""

    def test_post_then_get_returns_created_row(self, db_proxy: _NoCloseConn) -> None:
        """POST /data-entries then GET /data-entries SHALL include the created row.

        Requirements: 4.3
        """
        payload = {
            "year_month": "2025-03",
            "kwh": 350.5,
            "bill_amount": 4123.75,
            "label": "March bill",
            "source": "Manual",
        }

        with patch("api.main._get_db_conn", return_value=db_proxy):
            # Create the entry
            post_resp = client.post("/data-entries", json=payload)
            assert post_resp.status_code == 201, post_resp.text
            created = post_resp.json()

            # The POST response must echo back all submitted fields
            assert created["year_month"] == payload["year_month"]
            assert created["kwh"] == payload["kwh"]
            assert created["bill_amount"] == payload["bill_amount"]
            assert created["label"] == payload["label"]
            assert created["source"] == payload["source"]
            assert "id" in created
            assert "created_at" in created

            # Retrieve the list
            get_resp = client.get("/data-entries")
            assert get_resp.status_code == 200, get_resp.text
            rows = get_resp.json()

        # The created row must be present
        ids = [r["id"] for r in rows]
        assert created["id"] in ids, (
            f"Created row id={created['id']} not found in GET /data-entries response"
        )

        # Verify the specific row's values
        matching = [r for r in rows if r["id"] == created["id"]]
        assert len(matching) == 1
        row = matching[0]
        assert row["year_month"] == payload["year_month"]
        assert row["kwh"] == payload["kwh"]
        assert row["source"] == payload["source"]

    def test_post_minimal_fields_round_trip(self, db_proxy: _NoCloseConn) -> None:
        """POST /data-entries with only required fields SHALL persist and be retrievable.

        Requirements: 4.3
        """
        payload = {
            "year_month": "2025-06",
            "kwh": 200.0,
            "source": "CSV Upload",
        }

        with patch("api.main._get_db_conn", return_value=db_proxy):
            post_resp = client.post("/data-entries", json=payload)
            assert post_resp.status_code == 201, post_resp.text
            created = post_resp.json()

            assert created["bill_amount"] is None
            assert created["label"] is None

            get_resp = client.get("/data-entries")
            assert get_resp.status_code == 200
            rows = get_resp.json()

        matching = [r for r in rows if r["id"] == created["id"]]
        assert len(matching) == 1
        row = matching[0]
        assert row["year_month"] == "2025-06"
        assert row["kwh"] == 200.0
        assert row["source"] == "CSV Upload"

    def test_multiple_entries_all_appear_in_get(self, db_proxy: _NoCloseConn) -> None:
        """Multiple POSTed entries SHALL all appear in GET /data-entries.

        Requirements: 4.3
        """
        entries = [
            {"year_month": "2025-01", "kwh": 100.0, "source": "Manual"},
            {"year_month": "2025-02", "kwh": 200.0, "source": "Manual"},
            {"year_month": "2025-03", "kwh": 300.0, "source": "CSV Upload"},
        ]
        created_ids = []

        with patch("api.main._get_db_conn", return_value=db_proxy):
            for payload in entries:
                resp = client.post("/data-entries", json=payload)
                assert resp.status_code == 201
                created_ids.append(resp.json()["id"])

            get_resp = client.get("/data-entries")
            assert get_resp.status_code == 200
            rows = get_resp.json()

        returned_ids = {r["id"] for r in rows}
        for cid in created_ids:
            assert cid in returned_ids, f"Entry id={cid} missing from GET response"

    def test_get_returns_rows_ordered_descending_by_created_at(
        self, db_proxy: _NoCloseConn
    ) -> None:
        """GET /data-entries SHALL return rows ordered by created_at DESC.

        Requirements: 4.2
        """
        with patch("api.main._get_db_conn", return_value=db_proxy):
            for month in ["2025-01", "2025-02", "2025-03"]:
                resp = client.post(
                    "/data-entries",
                    json={"year_month": month, "kwh": 100.0, "source": "Manual"},
                )
                assert resp.status_code == 201

            get_resp = client.get("/data-entries")
            assert get_resp.status_code == 200
            rows = get_resp.json()

        created_ats = [r["created_at"] for r in rows]
        assert created_ats == sorted(created_ats, reverse=True), (
            "GET /data-entries rows are not ordered by created_at DESC"
        )


# ---------------------------------------------------------------------------
# 11.3  Chat history persistence
# ---------------------------------------------------------------------------


class TestChatHistoryPersistence:
    """Integration tests for POST → GET /chat-history round-trip (Requirements 5.2, 5.3)."""

    def test_post_then_get_returns_user_message(self, db_proxy: _NoCloseConn) -> None:
        """POST /chat-history then GET /chat-history SHALL include the user message.

        Requirements: 5.2, 5.3
        """
        payload = {"role": "user", "text": "What is my forecasted usage for next month?"}

        with patch("api.main._get_db_conn", return_value=db_proxy):
            post_resp = client.post("/chat-history", json=payload)
            assert post_resp.status_code == 201, post_resp.text
            created = post_resp.json()

            assert created["role"] == payload["role"]
            assert created["text"] == payload["text"]
            assert "id" in created
            assert "created_at" in created

            get_resp = client.get("/chat-history")
            assert get_resp.status_code == 200, get_resp.text
            messages = get_resp.json()

        ids = [m["id"] for m in messages]
        assert created["id"] in ids, (
            f"Created message id={created['id']} not found in GET /chat-history"
        )

        matching = [m for m in messages if m["id"] == created["id"]]
        assert len(matching) == 1
        msg = matching[0]
        assert msg["role"] == "user"
        assert msg["text"] == payload["text"]

    def test_post_then_get_returns_assistant_message(
        self, db_proxy: _NoCloseConn
    ) -> None:
        """POST /chat-history then GET /chat-history SHALL include the assistant message.

        Requirements: 5.2, 5.3
        """
        payload = {
            "role": "assistant",
            "text": "Based on the SARIMAX forecast, your usage next month is projected at 310 kWh.",
        }

        with patch("api.main._get_db_conn", return_value=db_proxy):
            post_resp = client.post("/chat-history", json=payload)
            assert post_resp.status_code == 201, post_resp.text
            created = post_resp.json()

            get_resp = client.get("/chat-history")
            assert get_resp.status_code == 200
            messages = get_resp.json()

        matching = [m for m in messages if m["id"] == created["id"]]
        assert len(matching) == 1
        assert matching[0]["role"] == "assistant"
        assert matching[0]["text"] == payload["text"]

    def test_exchange_persisted_in_chronological_order(
        self, db_proxy: _NoCloseConn
    ) -> None:
        """A user→assistant exchange SHALL appear in chronological order in GET response.

        Requirements: 5.2
        """
        user_payload = {"role": "user", "text": "How much will I spend in June?"}
        asst_payload = {
            "role": "assistant",
            "text": "Your projected bill for June 2025 is PHP 3,658.",
        }

        with patch("api.main._get_db_conn", return_value=db_proxy):
            user_resp = client.post("/chat-history", json=user_payload)
            assert user_resp.status_code == 201
            asst_resp = client.post("/chat-history", json=asst_payload)
            assert asst_resp.status_code == 201

            user_id = user_resp.json()["id"]
            asst_id = asst_resp.json()["id"]

            get_resp = client.get("/chat-history")
            assert get_resp.status_code == 200
            messages = get_resp.json()

        returned_ids = [m["id"] for m in messages]
        assert user_id in returned_ids
        assert asst_id in returned_ids

        user_pos = returned_ids.index(user_id)
        asst_pos = returned_ids.index(asst_id)
        assert user_pos < asst_pos, (
            "GET /chat-history: user message should appear before assistant message"
        )

    def test_get_chat_history_ordered_ascending(self, db_proxy: _NoCloseConn) -> None:
        """GET /chat-history SHALL return messages ordered by created_at ASC.

        Requirements: 5.2
        """
        with patch("api.main._get_db_conn", return_value=db_proxy):
            for i, role in enumerate(["user", "assistant", "user"]):
                resp = client.post(
                    "/chat-history",
                    json={"role": role, "text": f"Message {i}"},
                )
                assert resp.status_code == 201

            get_resp = client.get("/chat-history")
            assert get_resp.status_code == 200
            messages = get_resp.json()

        created_ats = [m["created_at"] for m in messages]
        assert created_ats == sorted(created_ats), (
            "GET /chat-history messages are not ordered by created_at ASC"
        )

    def test_post_invalid_role_returns_422(self) -> None:
        """POST /chat-history with invalid role SHALL return HTTP 422.

        Requirements: 5.3
        """
        resp = client.post("/chat-history", json={"role": "system", "text": "Hello"})
        assert resp.status_code == 422

    def test_post_empty_text_returns_422(self) -> None:
        """POST /chat-history with empty text SHALL return HTTP 422.

        Requirements: 5.3
        """
        resp = client.post("/chat-history", json={"role": "user", "text": ""})
        assert resp.status_code == 422

    def test_get_chat_history_limit_100(self, db_proxy: _NoCloseConn) -> None:
        """GET /chat-history SHALL return at most 100 messages.

        Requirements: 5.2
        """
        with patch("api.main._get_db_conn", return_value=db_proxy):
            # Insert 110 messages
            for i in range(110):
                role = "user" if i % 2 == 0 else "assistant"
                resp = client.post(
                    "/chat-history",
                    json={"role": role, "text": f"Message number {i + 1}"},
                )
                assert resp.status_code == 201

            get_resp = client.get("/chat-history")
            assert get_resp.status_code == 200
            messages = get_resp.json()

        assert len(messages) <= 100, (
            f"GET /chat-history returned {len(messages)} messages; max is 100"
        )
