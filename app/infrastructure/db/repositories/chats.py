"""Chat log repository — questions, answers, and retrieval traces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.infrastructure.db.models import ChatAnswer, ChatQuestion
from app.logging import get_logger

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger(__name__)


class ChatRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    # ── questions ────────────────────────────────────────────

    async def save_question(self, question: ChatQuestion) -> ChatQuestion:
        async with self._sf() as session:
            session.add(question)
            await session.commit()
            await session.refresh(question)
            session.expunge(question)
            return question

    async def get_question(self, question_id: uuid.UUID) -> ChatQuestion | None:
        async with self._sf() as session:
            q = await session.get(ChatQuestion, question_id)
            if q is not None:
                session.expunge(q)
            return q

    # ── answers ──────────────────────────────────────────────

    async def save_answer(self, answer: ChatAnswer) -> ChatAnswer:
        async with self._sf() as session:
            session.add(answer)
            await session.commit()
            await session.refresh(answer)
            session.expunge(answer)
            return answer

    async def get_answer(self, answer_id: uuid.UUID) -> ChatAnswer | None:
        async with self._sf() as session:
            a = await session.get(ChatAnswer, answer_id)
            if a is not None:
                session.expunge(a)
            return a

    async def get_answer_by_question(
        self,
        question_id: uuid.UUID,
    ) -> ChatAnswer | None:
        async with self._sf() as session:
            stmt = select(ChatAnswer).where(
                ChatAnswer.question_id == question_id,
            )
            result = await session.execute(stmt)
            a = result.scalar_one_or_none()
            if a is not None:
                session.expunge(a)
            return a
