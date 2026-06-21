"""
Unit tests for RAGService (rag/rag_service.py).

Covers:
  - Zero documents retrieved → "no forecast data" response; Ollama NOT called
  - Vector store unreachable → error response; Ollama NOT called
  - Ollama unreachable (ConnectError) → error response; no crash
  - Ollama timeout → timeout error response
  - Happy path: documents retrieved → prompt constructed → Ollama called →
    RAGResponse with answer + sources

Requirements: 6.1, 6.2, 6.3, 6.6, 6.7, 6.9, 6.10
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from pipeline.models import ForecastDocument, ForecastMetadata
from rag.rag_service import (
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    OLLAMA_URL,
    RAGResponse,
    RAGService,
)
from storage.vector_store import VectorStoreError


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_forecast_document(
    forecast_month: str = "2026-03",
    horizon_label: str = "3m",
    kwh: float = 320.5,
    price: float = 95.20,
) -> ForecastDocument:
    metadata = ForecastMetadata(
        forecast_month=forecast_month,
        forecasted_kwh=kwh,
        forecasted_price=price,
        horizon_label=horizon_label,
    )
    return ForecastDocument(
        id=f"{forecast_month}_{horizon_label}",
        text=(
            f"Forecast for {forecast_month} (horizon: {horizon_label}):\n"
            f"  Electricity consumption: {kwh:.2f} kWh\n"
            f"  Electricity price: £{price:.2f}"
        ),
        metadata=metadata,
    )


def _make_ollama_response(answer: str) -> dict:
    """Build a minimal Ollama /api/chat response dict."""
    return {
        "model": OLLAMA_MODEL,
        "message": {"role": "assistant", "content": answer},
        "done": True,
    }


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_vector_store():
    """Return a MagicMock that behaves like a VectorStore."""
    return MagicMock()


@pytest.fixture()
def rag_service(mock_vector_store):
    """RAGService wired to a mocked VectorStore."""
    return RAGService(vector_store=mock_vector_store)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestZeroDocuments:
    """When the vector store returns an empty list, Ollama must NOT be called."""

    def test_returns_no_forecast_data_message(self, rag_service, mock_vector_store):
        mock_vector_store.query.return_value = []

        with patch("httpx.Client") as mock_client_cls:
            result = rag_service.answer("What will my bill be in March 2026?")

        # Ollama must not be called
        mock_client_cls.assert_not_called()

        assert isinstance(result, RAGResponse)
        assert "no forecast data" in result.answer.lower()
        assert result.sources == []
        assert result.error is False

    def test_sources_are_empty(self, rag_service, mock_vector_store):
        mock_vector_store.query.return_value = []

        result = rag_service.answer("How much will I use next month?")

        assert result.sources == []


class TestVectorStoreUnreachable:
    """When the vector store raises an exception, return error without calling Ollama."""

    def test_vector_store_error_returns_error_response(self, rag_service, mock_vector_store):
        mock_vector_store.query.side_effect = VectorStoreError("ChromaDB unavailable")

        with patch("httpx.Client") as mock_client_cls:
            result = rag_service.answer("What is my forecast?")

        mock_client_cls.assert_not_called()

        assert isinstance(result, RAGResponse)
        assert result.error is True
        assert "vector store" in result.answer.lower() or "retrieval failed" in result.answer.lower()
        assert result.sources == []

    def test_generic_exception_from_vector_store(self, rag_service, mock_vector_store):
        mock_vector_store.query.side_effect = RuntimeError("Connection refused")

        with patch("httpx.Client") as mock_client_cls:
            result = rag_service.answer("What is my forecast?")

        mock_client_cls.assert_not_called()
        assert result.error is True

    def test_no_crash_on_vector_store_error(self, rag_service, mock_vector_store):
        """Must not propagate any exception to the caller."""
        mock_vector_store.query.side_effect = Exception("Unexpected DB failure")

        try:
            result = rag_service.answer("test question")
        except Exception as exc:
            pytest.fail(f"RAGService.answer() raised an unexpected exception: {exc}")

        assert result.error is True


class TestOllamaUnreachable:
    """When Ollama raises a ConnectError, return error response without crashing."""

    def test_ollama_connect_error_returns_error_response(self, rag_service, mock_vector_store):
        docs = [_make_forecast_document()]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.side_effect = httpx.ConnectError("Connection refused")

            result = rag_service.answer("What is my forecast?")

        assert isinstance(result, RAGResponse)
        assert result.error is True
        assert "unavailable" in result.answer.lower() or "ollama" in result.answer.lower()

    def test_no_crash_on_ollama_connect_error(self, rag_service, mock_vector_store):
        docs = [_make_forecast_document()]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.side_effect = httpx.ConnectError("Connection refused")

            try:
                result = rag_service.answer("test question")
            except Exception as exc:
                pytest.fail(f"RAGService.answer() raised an unexpected exception: {exc}")

        assert result.error is True


class TestOllamaTimeout:
    """When Ollama times out, return a timeout error response."""

    def test_timeout_returns_error_response(self, rag_service, mock_vector_store):
        docs = [_make_forecast_document()]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.side_effect = httpx.TimeoutException("Request timed out")

            result = rag_service.answer("What is my forecast?")

        assert isinstance(result, RAGResponse)
        assert result.error is True
        assert "timeout" in result.answer.lower() or "too long" in result.answer.lower()

    def test_timeout_error_includes_timeout_duration(self, rag_service, mock_vector_store):
        docs = [_make_forecast_document()]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.side_effect = httpx.TimeoutException("timed out")

            result = rag_service.answer("test question")

        # The answer should mention the timeout duration
        assert str(int(OLLAMA_TIMEOUT_SECONDS)) in result.answer

    def test_no_crash_on_timeout(self, rag_service, mock_vector_store):
        docs = [_make_forecast_document()]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.side_effect = httpx.TimeoutException("timed out")

            try:
                result = rag_service.answer("test question")
            except Exception as exc:
                pytest.fail(f"RAGService.answer() raised an unexpected exception: {exc}")

        assert result.error is True


class TestHappyPath:
    """Documents retrieved → prompt built → Ollama called → RAGResponse with answer + sources."""

    def _make_mock_http_response(self, answer_text: str) -> MagicMock:
        mock_response = MagicMock()
        mock_response.json.return_value = _make_ollama_response(answer_text)
        mock_response.raise_for_status = MagicMock()
        return mock_response

    def test_answer_contains_llm_text(self, rag_service, mock_vector_store):
        expected_answer = "Your forecast for March 2026 is 320.5 kWh."
        docs = [_make_forecast_document()]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.return_value = self._make_mock_http_response(expected_answer)

            result = rag_service.answer("What is my forecast for March 2026?")

        assert result.answer == expected_answer
        assert result.error is False

    def test_sources_match_retrieved_documents(self, rag_service, mock_vector_store):
        docs = [
            _make_forecast_document("2026-03", "3m"),
            _make_forecast_document("2026-04", "3m"),
            _make_forecast_document("2026-05", "3m"),
        ]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.return_value = self._make_mock_http_response("The answer.")

            result = rag_service.answer("Summarise my forecast")

        assert len(result.sources) == 3
        assert all(isinstance(s, ForecastMetadata) for s in result.sources)
        months = {s.forecast_month for s in result.sources}
        assert months == {"2026-03", "2026-04", "2026-05"}

    def test_ollama_called_with_correct_url_and_model(self, rag_service, mock_vector_store):
        docs = [_make_forecast_document()]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.return_value = self._make_mock_http_response("answer")

            rag_service.answer("test question")

        call_kwargs = mock_client_instance.post.call_args
        assert call_kwargs is not None

        # Verify URL
        called_url = call_kwargs[0][0] if call_kwargs[0] else call_kwargs.kwargs.get("url")
        if called_url is None:
            # Try positional arg in args list
            called_url = call_kwargs.args[0]
        assert called_url == OLLAMA_URL

        # Verify model in payload
        sent_json = call_kwargs.kwargs.get("json") or (call_kwargs[1].get("json") if len(call_kwargs) > 1 else None)
        assert sent_json is not None
        assert sent_json["model"] == OLLAMA_MODEL
        assert sent_json["stream"] is False
        assert sent_json["options"]["temperature"] == 0.1

    def test_ollama_called_with_30s_timeout(self, rag_service, mock_vector_store):
        docs = [_make_forecast_document()]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.return_value = self._make_mock_http_response("answer")

            rag_service.answer("test question")

        # httpx.Client is instantiated with timeout=OLLAMA_TIMEOUT_SECONDS
        mock_client_cls.assert_called_once_with(timeout=OLLAMA_TIMEOUT_SECONDS)

    def test_prompt_contains_question_and_document_text(self, rag_service, mock_vector_store):
        question = "How much will I use in March 2026?"
        doc = _make_forecast_document("2026-03", "3m", kwh=320.5, price=95.20)
        mock_vector_store.query.return_value = [doc]

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.return_value = self._make_mock_http_response("answer")

            rag_service.answer(question)

        sent_json = mock_client_instance.post.call_args.kwargs["json"]
        prompt_content = sent_json["messages"][0]["content"]

        assert question in prompt_content
        assert doc.text in prompt_content

    def test_top_5_retrieved_from_vector_store(self, rag_service, mock_vector_store):
        docs = [_make_forecast_document()]
        mock_vector_store.query.return_value = docs

        with patch("httpx.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client_instance.post.return_value = self._make_mock_http_response("answer")

            rag_service.answer("test question")

        mock_vector_store.query.assert_called_once_with("test question", top_k=5)
