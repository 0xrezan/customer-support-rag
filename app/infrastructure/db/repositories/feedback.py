"""Feedback repository — thumbs up/down persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from app.infrastructure.db.models import FeedbackEvent, FeedbackRating
from app.logging import get_logger

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger(__name__)


class FeedbackRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def create(self, event: FeedbackEvent) -> FeedbackEvent:
        async with self._sf() as session:
            session.add(event)
            await session.commit()
            await session.refresh(event)
            session.expunge(event)
            logger.info("feedback.saved", answer_id=str(event.answer_id), rating=event.rating)
            return event

    async def get_by_answer(
        self,
        answer_id: uuid.UUID,
    ) -> list[FeedbackEvent]:
        async with self._sf() as session:
            stmt = select(FeedbackEvent).where(
                FeedbackEvent.answer_id == answer_id,
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_by_rating(
        self,
        answer_id: uuid.UUID,
        rating: FeedbackRating,
    ) -> int:
        async with self._sf() as session:
            stmt = (
                select(func.count())
                .select_from(FeedbackEvent)
                .where(
                    FeedbackEvent.answer_id == answer_id,
                    FeedbackEvent.rating == rating,
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one()
