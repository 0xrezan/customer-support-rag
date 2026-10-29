"""End-to-end test — Telegram chat flow with mocked aiogram.

Tests bot handler logic without requiring a live Telegram connection.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.bot.routers.user_chat import handle_question
from app.domain.value_objects.answer_result import AnswerResult, AnswerStatusEnum, Citation


def _make_container() -> MagicMock:
    container = MagicMock()
    container.query_service = AsyncMock()
    return container


def _make_message(text: str = "What is the return policy?") -> MagicMock:
    """Create a mock aiogram Message."""
    message = AsyncMock()
    message.text = text
    message.from_user = MagicMock()
    message.from_user.id = 123456
    message.answer = AsyncMock()
    return message


@pytest.mark.e2e
class TestTelegramChatFlow:
    async def test_message_gets_answer(self) -> None:
        """Send a message to the handler and verify a response is returned."""
        container = _make_container()
        answer_id = uuid.uuid4()
        container.query_service.ask.return_value = AnswerResult(
            status=AnswerStatusEnum.ANSWERED,
            text="You can return items within 30 days.",
            citations=[
                Citation(document_name="policy.pdf", page=3, chunk_id="c1"),
            ],
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            latency_ms=150,
            answer_id=answer_id,
        )

        message = _make_message()
        await handle_question(message, container=container)

        # Handler should call query_service.ask
        container.query_service.ask.assert_called_once_with(
            "What is the return policy?",
            source="telegram",
            user_id="123456",
        )

        # Handler should send a reply
        message.answer.assert_called_once()
        call_args = message.answer.call_args
        reply_text = call_args[0][0]
        assert "30 days" in reply_text

        # Should include feedback keyboard
        reply_markup = (
            call_args[1].get("reply_markup")
            if len(call_args) > 1
            else call_args.kwargs.get("reply_markup")
        )
        assert reply_markup is not None

    async def test_message_without_container_returns_unavailable(self) -> None:
        """When container is not available, bot should reply with service unavailable."""
        message = _make_message()
        await handle_question(message, container=None)

        message.answer.assert_called_once_with("Service unavailable. Please try again later.")

    async def test_empty_message_ignored(self) -> None:
        """Handler should do nothing for messages without text."""
        message = _make_message()
        message.text = None

        await handle_question(message, container=_make_container())

        # query_service should not be called
        message.answer.assert_not_called()

    async def test_insufficient_context_no_feedback_buttons(self) -> None:
        """When answer has no answer_id (e.g. insufficient context), no feedback buttons."""
        container = _make_container()
        container.query_service.ask.return_value = AnswerResult(
            status=AnswerStatusEnum.INSUFFICIENT_CONTEXT,
            text="I don't have enough information to answer that.",
            latency_ms=50,
            answer_id=None,
        )

        message = _make_message("What is the meaning of life?")
        await handle_question(message, container=container)

        message.answer.assert_called_once()
        call_args = message.answer.call_args
        reply_markup = call_args.kwargs.get("reply_markup")
        # No feedback buttons for insufficient context when answer_id is None
        assert reply_markup is None
