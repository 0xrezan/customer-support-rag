"""Document repository — CRUD, row locking, status transitions, active version ops."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy import select, update

from app.infrastructure.db.models import Document, DocumentStatus
from app.logging import get_logger

if TYPE_CHECKING:
    import uuid
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger(__name__)


class DocumentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    # ── queries ──────────────────────────────────────────────

    async def get_by_id(self, doc_id: uuid.UUID) -> Document | None:
        async with self._sf() as session:
            doc = await session.get(Document, doc_id)
            if doc is not None:
                session.expunge(doc)
            return doc

    async def get_by_hash(self, content_hash: str) -> Document | None:
        async with self._sf() as session:
            stmt = (
                select(Document)
                .where(Document.content_hash == content_hash)
                .order_by(Document.version.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            doc = result.scalar_one_or_none()
            if doc is not None:
                session.expunge(doc)
            return doc

    async def list_active(self) -> list[Document]:
        async with self._sf() as session:
            stmt = select(Document).where(
                Document.is_active_version.is_(True),
                Document.status == DocumentStatus.INDEXED,
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def list_all(self) -> list[Document]:
        async with self._sf() as session:
            stmt = select(Document).order_by(Document.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ── mutations ────────────────────────────────────────────

    async def create(self, doc: Document) -> Document:
        async with self._sf() as session:
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            session.expunge(doc)
            return doc

    async def set_status(
        self,
        doc_id: uuid.UUID,
        status: DocumentStatus,
        *,
        error_message: str | None = None,
    ) -> None:
        async with self._sf() as session:
            values: dict = {"status": status}
            if error_message is not None:
                values["error_message"] = error_message
            stmt = update(Document).where(Document.id == doc_id).values(**values)
            await session.execute(stmt)
            await session.commit()
            logger.info("document.status_changed", doc_id=str(doc_id), status=status)

    async def set_chunk_counts(
        self,
        doc_id: uuid.UUID,
        *,
        expected: int,
        actual: int,
    ) -> None:
        async with self._sf() as session:
            stmt = (
                update(Document)
                .where(Document.id == doc_id)
                .values(chunk_count_expected=expected, chunk_count_actual=actual)
            )
            await session.execute(stmt)
            await session.commit()

    async def activate_version(self, doc_id: uuid.UUID, version: int) -> None:
        """Mark a specific version as active and deactivate others for the same hash."""
        async with self._sf() as session:
            doc = await session.get(Document, doc_id)
            if doc is None:
                return
            # Deactivate all versions with the same content_hash
            stmt = (
                update(Document)
                .where(
                    Document.content_hash == doc.content_hash,
                    Document.is_active_version.is_(True),
                )
                .values(is_active_version=False)
            )
            await session.execute(stmt)
            # Activate the target version
            stmt = (
                update(Document)
                .where(Document.id == doc_id, Document.version == version)
                .values(is_active_version=True)
            )
            await session.execute(stmt)
            await session.commit()
            logger.info(
                "document.version_activated",
                doc_id=str(doc_id),
                version=version,
            )

    async def lock_for_update(self, doc_id: uuid.UUID) -> Document | None:
        """SELECT … FOR UPDATE (non-contextual, lock released immediately).

        .. deprecated::
            Use :meth:`lock_for_processing` instead so the row lock is held
            for the duration of the caller's work.
        """
        async with self._sf() as session:
            stmt = select(Document).where(Document.id == doc_id).with_for_update()
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @asynccontextmanager
    async def lock_for_processing(self, doc_id: uuid.UUID) -> AsyncIterator[Document | None]:
        """Acquire a ``SELECT … FOR UPDATE`` lock and hold it until the caller exits.

        Usage::

            async with doc_repo.lock_for_processing(doc_uuid) as doc:
                if doc is None:
                    return
                # … do work while the row lock is held …

        The lock is released (and the transaction committed) when the block
        exits.  On exception the transaction is rolled back automatically.
        """
        async with self._sf() as session:
            stmt = select(Document).where(Document.id == doc_id).with_for_update()
            result = await session.execute(stmt)
            doc = result.scalar_one_or_none()
            try:
                yield doc
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def soft_delete(self, doc_id: uuid.UUID) -> None:
        await self.set_status(doc_id, DocumentStatus.DELETED)

    async def hard_delete(self, doc_id: uuid.UUID) -> bool:
        """Permanently remove a document row from the database.

        Returns True if a row was deleted.
        """
        from sqlalchemy import delete as sa_delete

        async with self._sf() as session:
            stmt = sa_delete(Document).where(Document.id == doc_id)
            result = await session.execute(stmt)
            await session.commit()
            deleted = (getattr(result, "rowcount", 0) or 0) > 0
            if deleted:
                logger.info("document.hard_deleted", doc_id=str(doc_id))
            return deleted

    async def list_by_knowledge_base(self, kb_id: uuid.UUID) -> list[Document]:
        """List documents filtered by knowledge_base_id (Phase 2 multi-tenant).

        .. note::
            Requires ``knowledge_base_id`` FK on the ``Document`` model.
            Until the FK is added, this method filters by the column if it
            exists, otherwise returns all non-deleted documents with a warning.
        """
        async with self._sf() as session:
            stmt = select(Document).where(Document.status != DocumentStatus.DELETED)
            if hasattr(Document, "knowledge_base_id"):
                stmt = stmt.where(Document.knowledge_base_id == kb_id)  # type: ignore[attr-defined]
            else:
                logger.warning(
                    "document.list_by_kb_unfiltered",
                    kb_id=str(kb_id),
                    reason="knowledge_base_id FK not yet on Document model",
                )
            stmt = stmt.order_by(Document.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
