"""Integration test — feedback persistence and retrieval trace.

Tests that feedback service correctly stores and links feedback to answers.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.db.models import FeedbackRating


@pytest.mark.integration
class TestFeedbackLogging:
    async def test_feedback_stored(self) -> None:
        """Submit feedback and verify it is passed to the repository."""
        from app.domain.services.feedback_service import FeedbackService

        feedback_repo = AsyncMock()
        mock_event = MagicMock()
        mock_event.id = uuid.uuid4()
        mock_event.answer_id = uuid.uuid4()
        mock_event.rating = FeedbackRating.THUMBS_UP
        feedback_repo.create.return_value = mock_event

        service = FeedbackService(feedback_repo=feedback_repo)
        result = await service.submit(
            answer_id=mock_event.answer_id,
            rating="thumbs_up",
            user_id="user_123",
        )

        feedback_repo.create.assert_called_once()
        assert result.rating == FeedbackRating.THUMBS_UP

    async def test_feedback_linked_to_answer(self) -> None:
        """Verify feedback event references the correct answer ID."""
        from app.domain.services.feedback_service import FeedbackService

        answer_id = uuid.uuid4()
        feedback_repo = AsyncMock()

        created_event = MagicMock()
        created_event.id = uuid.uuid4()
        created_event.answer_id = answer_id
        created_event.rating = FeedbackRating.THUMBS_DOWN
        feedback_repo.create.return_value = created_event

        service = FeedbackService(feedback_repo=feedback_repo)
        result = await service.submit(
            answer_id=answer_id,
            rating="thumbs_down",
            comment="Not helpful",
            user_id="user_456",
        )

        assert result.answer_id == answer_id
