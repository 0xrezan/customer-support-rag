"""Ingestion job repository — job state persistence and locking helpers."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy import insert, select, update

from app.infrastructure.db.models import IngestionJob, JobStatus
from app.logging import get_logger
from app.utils.time import utc_now

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger(__name__)


class IngestionJobRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def create(self, job: IngestionJob) -> IngestionJob:
        async with self._sf() as session:
            session.add(job)
            await session.commit()
            await session.refresh(job)
            session.expunge(job)
            return job

    async def create_for_document(self, document_id: uuid.UUID) -> uuid.UUID:
        """Create a pending ingestion job via raw INSERT (bypasses ORM dataclass issues)."""
        job_id = uuid.uuid4()
        async with self._sf() as session:
            stmt = insert(IngestionJob.__table__).values(
                id=job_id,
                document_id=document_id,
                status="pending",
                attempts=0,
            )
            await session.execute(stmt)
            await session.commit()
        return job_id

    async def get_by_id(self, job_id: uuid.UUID) -> IngestionJob | None:
        async with self._sf() as session:
            job = await session.get(IngestionJob, job_id)
            if job is not None:
                session.expunge(job)
            return job

    async def get_pending_for_document(
        self,
        document_id: uuid.UUID,
    ) -> IngestionJob | None:
        async with self._sf() as session:
            stmt = (
                select(IngestionJob)
                .where(
                    IngestionJob.document_id == document_id,
                    IngestionJob.status == JobStatus.PENDING,
                )
                .limit(1)
            )
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()
            if job is not None:
                session.expunge(job)
            return job

    async def mark_running(self, job_id: uuid.UUID) -> None:
        async with self._sf() as session:
            stmt = (
                update(IngestionJob)
                .where(IngestionJob.id == job_id)
                .values(
                    status=JobStatus.RUNNING,
                    started_at=utc_now(),
                    attempts=IngestionJob.attempts + 1,
                )
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("job.running", job_id=str(job_id))

    async def mark_completed(self, job_id: uuid.UUID) -> None:
        async with self._sf() as session:
            stmt = (
                update(IngestionJob)
                .where(IngestionJob.id == job_id)
                .values(status=JobStatus.COMPLETED, finished_at=utc_now())
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("job.completed", job_id=str(job_id))

    async def mark_failed(
        self,
        job_id: uuid.UUID,
        *,
        error_message: str,
    ) -> None:
        async with self._sf() as session:
            stmt = (
                update(IngestionJob)
                .where(IngestionJob.id == job_id)
                .values(
                    status=JobStatus.FAILED,
                    finished_at=utc_now(),
                    error_message=error_message,
                )
            )
            await session.execute(stmt)
            await session.commit()
            logger.warning("job.failed", job_id=str(job_id), error=error_message)

    async def lock_for_update(self, job_id: uuid.UUID) -> IngestionJob | None:
        """SELECT … FOR UPDATE (non-contextual, lock released immediately).

        .. deprecated::
            Use :meth:`lock_for_processing` for long-lived row locks.
        """
        async with self._sf() as session:
            stmt = select(IngestionJob).where(IngestionJob.id == job_id).with_for_update()
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @asynccontextmanager
    async def lock_for_processing(self, job_id: uuid.UUID) -> AsyncIterator[IngestionJob | None]:
        """Hold a ``SELECT … FOR UPDATE`` lock for the lifetime of the block."""
        async with self._sf() as session:
            stmt = select(IngestionJob).where(IngestionJob.id == job_id).with_for_update()
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()
            if job is not None:
                session.expunge(job)
            try:
                yield job
                await session.commit()
            except Exception:
                await session.rollback()
                raise
