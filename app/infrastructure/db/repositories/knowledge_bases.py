"""Knowledge base repository — multi-tenant KB management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, update

from app.infrastructure.db.models_phase2 import KnowledgeBaseModel
from app.logging import get_logger

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger(__name__)


class KnowledgeBaseRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_by_id(self, kb_id: uuid.UUID) -> KnowledgeBaseModel | None:
        async with self._sf() as session:
            kb = await session.get(KnowledgeBaseModel, kb_id)
            if kb is not None:
                session.expunge(kb)
            return kb

    async def get_by_name(self, name: str) -> KnowledgeBaseModel | None:
        async with self._sf() as session:
            stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.name == name).limit(1)
            result = await session.execute(stmt)
            kb = result.scalar_one_or_none()
            if kb is not None:
                session.expunge(kb)
            return kb

    async def list_active(self) -> list[KnowledgeBaseModel]:
        async with self._sf() as session:
            stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.is_active.is_(True))
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(self, kb: KnowledgeBaseModel) -> KnowledgeBaseModel:
        async with self._sf() as session:
            session.add(kb)
            await session.commit()
            await session.refresh(kb)
            session.expunge(kb)
            return kb

    async def deactivate(self, kb_id: uuid.UUID) -> None:
        async with self._sf() as session:
            stmt = (
                update(KnowledgeBaseModel)
                .where(KnowledgeBaseModel.id == kb_id)
                .values(is_active=False)
            )
            await session.execute(stmt)
            await session.commit()
