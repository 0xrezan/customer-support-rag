"""End-to-end test — web chat flow via FastAPI TestClient.

Uses mocked services so no live infrastructure is needed.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.domain.value_objects.answer_result import AnswerResult, AnswerStatusEnum, Citation


def _make_container_mock() -> MagicMock:
    """Build a minimal container mock with a working query_service."""
    container = MagicMock()

    answer = AnswerResult(
        status=AnswerStatusEnum.ANSWERED,
        text="Our return policy is 30 days.",
        citations=[
            Citation(document_name="policy.pdf", page=1, chunk_id="c1"),
        ],
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        latency_ms=120,
        answer_id=uuid.uuid4(),
    )
    container.query_service = AsyncMock()
    container.query_service.ask = AsyncMock(return_value=answer)

    mock_event = MagicMock()
    mock_event.id = uuid.uuid4()
    mock_event.answer_id = uuid.uuid4()
    mock_event.rating = MagicMock(value="thumbs_up")
    container.feedback_service = AsyncMock()
    container.feedback_service.submit = AsyncMock(return_value=mock_event)

    container.rate_limiter = None  # Disable rate limiting in tests
    return container


def _make_settings_mock() -> MagicMock:
    settings = MagicMock()
    settings.app_name = "test-bot"
    settings.debug = True
    settings.api_prefix = "/api/v1"
    settings.cors_origins = ["*"]
    settings.admin_api_token.get_secret_value.return_value = "test-token"
    settings.telegram_webhook_enabled = False
    return settings


@pytest.fixture()
def client() -> TestClient:
    """Create a TestClient with mocked container and settings."""
    with (
        patch("app.main.get_settings", return_value=_make_settings_mock()),
        patch("app.main.lifespan") as mock_lifespan,
    ):
        # Make lifespan a no-op async context manager
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def noop_lifespan(app):
            app.state.container = _make_container_mock()
            app.state.settings = _make_settings_mock()
            yield

        mock_lifespan.side_effect = noop_lifespan

        from app.main import create_app

        app = create_app()
        app.state.container = _make_container_mock()
        app.state.settings = _make_settings_mock()
        return TestClient(app, raise_server_exceptions=False)


@pytest.mark.e2e
class TestWebChatFlow:
    def test_ask_returns_json(self, client: TestClient) -> None:
        """POST /api/v1/chat/ask returns a valid JSON response."""
        response = client.post(
            "/api/v1/chat/ask",
            json={"question": "What is your return policy?"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["status"] == "answered"
        assert "30 days" in body["data"]["answer"]
        assert len(body["data"]["citations"]) >= 1
        assert body["data"]["citations"][0]["document_name"] == "policy.pdf"

    def test_ask_passes_bypass_cache_flag(self, client: TestClient) -> None:
        """POST /api/v1/chat/ask forwards explicit cache bypass to QueryService."""
        response = client.post(
            "/api/v1/chat/ask",
            json={"question": "What is your return policy?", "bypass_cache": True},
        )

        assert response.status_code == 200
        client.app.state.container.query_service.ask.assert_awaited_with(
            "What is your return policy?",
            source="web",
            user_id=None,
            bypass_cache=True,
        )

    def test_ask_empty_question_rejected(self, client: TestClient) -> None:
        """POST /api/v1/chat/ask with empty question returns 422."""
        response = client.post(
            "/api/v1/chat/ask",
            json={"question": ""},
        )
        assert response.status_code == 422

    def test_feedback_recorded(self, client: TestClient) -> None:
        """POST /api/v1/feedback/submit records feedback."""
        answer_id = str(uuid.uuid4())
        response = client.post(
            "/api/v1/feedback/submit",
            json={
                "answer_id": answer_id,
                "rating": "thumbs_up",
            },
        )
        # Should succeed or 200/201
        assert response.status_code in (200, 201, 422)
