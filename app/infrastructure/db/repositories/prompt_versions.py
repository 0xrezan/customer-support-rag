"""Prompt version repository — CRUD for prompt templates in SQL."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, update

from app.infrastructure.db.models_phase2 import PromptVersion
from app.logging import get_logger

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger(__name__)


class PromptVersionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_active(self, name: str) -> PromptVersion | None:
        """Get the currently active prompt version by name."""
        async with self._sf() as session:
            stmt = (
                select(PromptVersion)
                .where(PromptVersion.name == name, PromptVersion.is_active.is_(True))
                .limit(1)
            )
            result = await session.execute(stmt)
            prompt = result.scalar_one_or_none()
            if prompt is not None:
                session.expunge(prompt)
            return prompt

    async def list_by_name(self, name: str) -> list[PromptVersion]:
        async with self._sf() as session:
            stmt = select(PromptVersion).where(PromptVersion.name == name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(self, prompt: PromptVersion) -> PromptVersion:
        async with self._sf() as session:
            session.add(prompt)
            await session.commit()
            await session.refresh(prompt)
            session.expunge(prompt)
            return prompt

    async def activate(self, prompt_id: uuid.UUID) -> None:
        """Activate a version and deactivate all others with the same name."""
        async with self._sf() as session:
            prompt = await session.get(PromptVersion, prompt_id)
            if prompt is None:
                return
            # Deactivate all versions with the same name
            stmt = (
                update(PromptVersion)
                .where(PromptVersion.name == prompt.name)
                .values(is_active=False)
            )
            await session.execute(stmt)
            # Activate the target
            stmt = (
                update(PromptVersion).where(PromptVersion.id == prompt_id).values(is_active=True)
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("prompt_version.activated", id=str(prompt_id), name=prompt.name)
