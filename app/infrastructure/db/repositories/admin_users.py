"""Admin user repository — RBAC user management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, update

from app.infrastructure.db.models_phase2 import AdminUser
from app.logging import get_logger

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger(__name__)


class AdminUserRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_by_id(self, user_id: uuid.UUID) -> AdminUser | None:
        async with self._sf() as session:
            user = await session.get(AdminUser, user_id)
            if user is not None:
                session.expunge(user)
            return user

    async def get_by_username(self, username: str) -> AdminUser | None:
        async with self._sf() as session:
            stmt = select(AdminUser).where(AdminUser.username == username).limit(1)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user is not None:
                session.expunge(user)
            return user

    async def get_by_token_hash(self, token_hash: str) -> AdminUser | None:
        async with self._sf() as session:
            stmt = (
                select(AdminUser)
                .where(AdminUser.api_token_hash == token_hash, AdminUser.is_active.is_(True))
                .limit(1)
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user is not None:
                session.expunge(user)
            return user

    async def get_by_telegram_id(self, telegram_id: int) -> AdminUser | None:
        async with self._sf() as session:
            stmt = select(AdminUser).where(AdminUser.telegram_id == telegram_id).limit(1)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user is not None:
                session.expunge(user)
            return user

    async def list_all(self) -> list[AdminUser]:
        async with self._sf() as session:
            stmt = select(AdminUser).order_by(AdminUser.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(self, user: AdminUser) -> AdminUser:
        async with self._sf() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            session.expunge(user)
            return user

    async def deactivate(self, user_id: uuid.UUID) -> None:
        async with self._sf() as session:
            stmt = update(AdminUser).where(AdminUser.id == user_id).values(is_active=False)
            await session.execute(stmt)
            await session.commit()
