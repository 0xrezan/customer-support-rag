"""Persist feedback linked to answer and retrieval trace."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.infrastructure.db.models import FeedbackEvent, FeedbackRating
from app.infrastructure.telemetry.metrics import increment_feedback
from app.logging import get_logger

if TYPE_CHECKING:
    import uuid

    from app.infrastructure.db.repositories.feedback import FeedbackRepository

logger = get_logger(__name__)


class FeedbackService:
    def __init__(self, feedback_repo: FeedbackRepository) -> None:
        self._repo = feedback_repo

    async def submit(
        self,
        answer_id: uuid.UUID,
        rating: str,
        *,
        comment: str | None = None,
        user_id: str | None = None,
    ) -> FeedbackEvent:
        """Record a feedback event."""
        feedback_rating = FeedbackRating(rating)
        event = FeedbackEvent(
            answer_id=answer_id,
            rating=feedback_rating,
            comment=comment,
            user_id=user_id,
        )
        saved = await self._repo.create(event)
        increment_feedback(rating)
        logger.info(
            "feedback.submitted",
            answer_id=str(answer_id),
            rating=rating,
        )
        return saved
