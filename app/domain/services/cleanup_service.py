"""Background cleanup and archival policies for old chat logs."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from app.infrastructure.db.models import ChatAnswer, ChatQuestion, FeedbackEvent
from app.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger(__name__)


class CleanupService:
    """Archive and purge old chat logs according to retention policy."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        retention_days: int = 90,
    ) -> None:
        self._sf = session_factory
        self._retention_days = retention_days

    async def purge_old_chats(self) -> dict[str, int]:
        """Delete chat questions, answers, and feedback older than retention period.

        Returns counts of deleted rows.
        """
        from app.utils.time import utc_now

        cutoff = utc_now() - timedelta(days=self._retention_days)
        summary = {"questions": 0, "answers": 0, "feedback": 0}

        async with self._sf() as session:
            # Find old question IDs
            old_questions_stmt = select(ChatQuestion.id).where(ChatQuestion.created_at < cutoff)
            result = await session.execute(old_questions_stmt)
            old_q_ids = [row[0] for row in result]

            if not old_q_ids:
                logger.info("cleanup.nothing_to_purge")
                return summary

            # Delete feedback for answers of old questions
            old_answers_stmt = select(ChatAnswer.id).where(ChatAnswer.question_id.in_(old_q_ids))
            result = await session.execute(old_answers_stmt)
            old_a_ids = [row[0] for row in result]

            if old_a_ids:
                fb_del = await session.execute(
                    delete(FeedbackEvent).where(FeedbackEvent.answer_id.in_(old_a_ids))
                )
                summary["feedback"] = fb_del.rowcount or 0

            # Delete answers
            ans_del = await session.execute(
                delete(ChatAnswer).where(ChatAnswer.question_id.in_(old_q_ids))
            )
            summary["answers"] = ans_del.rowcount or 0

            # Delete questions
            q_del = await session.execute(
                delete(ChatQuestion).where(ChatQuestion.id.in_(old_q_ids))
            )
            summary["questions"] = q_del.rowcount or 0

            await session.commit()

        logger.info("cleanup.purged", **summary, cutoff=cutoff.isoformat())
        return summary
