"""Unanswered-question report generation by document and topic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from app.infrastructure.db.models import AnswerStatus, ChatAnswer, ChatQuestion
from app.logging import get_logger

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger(__name__)


@dataclass
class UnansweredReport:
    """Summary of unanswered questions in a time range."""

    total_questions: int = 0
    answered: int = 0
    insufficient_context: int = 0
    errors: int = 0
    unanswered_rate: float = 0.0
    top_unanswered: list[dict[str, str]] = field(default_factory=list)


class ReportService:
    """Generates reports over chat logs and feedback data."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def unanswered_report(
        self,
        *,
        since: datetime | None = None,
        limit: int = 50,
    ) -> UnansweredReport:
        """Generate unanswered-question report."""
        async with self._sf() as session:
            # Total counts by status
            base = select(
                ChatAnswer.status,
                func.count().label("cnt"),
            ).group_by(ChatAnswer.status)

            if since:
                base = base.where(ChatAnswer.created_at >= since)

            result = await session.execute(base)
            counts = {row.status: row.cnt for row in result}

            answered = counts.get(AnswerStatus.ANSWERED, 0)
            insufficient = counts.get(AnswerStatus.INSUFFICIENT_CONTEXT, 0)
            errors = counts.get(AnswerStatus.ERROR, 0)
            total = answered + insufficient + errors
            unanswered_rate = (insufficient + errors) / total if total > 0 else 0.0

            # Top unanswered questions
            top_stmt = (
                select(ChatQuestion.question_text, ChatAnswer.status)
                .join(ChatAnswer, ChatAnswer.question_id == ChatQuestion.id)
                .where(
                    ChatAnswer.status.in_(
                        [
                            AnswerStatus.INSUFFICIENT_CONTEXT,
                            AnswerStatus.ERROR,
                        ]
                    )
                )
                .order_by(ChatQuestion.created_at.desc())
                .limit(limit)
            )
            if since:
                top_stmt = top_stmt.where(ChatQuestion.created_at >= since)

            top_result = await session.execute(top_stmt)
            top_unanswered = [
                {"question": row.question_text, "status": row.status.value} for row in top_result
            ]

            report = UnansweredReport(
                total_questions=total,
                answered=answered,
                insufficient_context=insufficient,
                errors=errors,
                unanswered_rate=round(unanswered_rate, 4),
                top_unanswered=top_unanswered,
            )

            logger.info(
                "report.unanswered",
                total=total,
                unanswered_rate=report.unanswered_rate,
            )
            return report

    async def feedback_summary(
        self,
        *,
        since: datetime | None = None,
    ) -> dict[str, int]:
        """Count feedback by rating."""
        from app.infrastructure.db.models import FeedbackEvent

        async with self._sf() as session:
            stmt = select(
                FeedbackEvent.rating,
                func.count().label("cnt"),
            ).group_by(FeedbackEvent.rating)

            if since:
                stmt = stmt.where(FeedbackEvent.created_at >= since)

            result = await session.execute(stmt)
            return {row.rating.value: row.cnt for row in result}
