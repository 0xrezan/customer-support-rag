"""Background Dramatiq task handlers.

Each task is a thin wrapper that builds the required services and delegates
to domain logic.  Heavy lifting stays in domain/services.
"""

from __future__ import annotations

import asyncio
import uuid

import dramatiq

from app.config import get_settings
from app.infrastructure.queue.broker import setup_broker
from app.logging import get_logger

logger = get_logger(__name__)

# Ensure the broker is initialised when this module is imported by the worker.
_settings = get_settings()
setup_broker(_settings.dramatiq_broker_url)


def _run_async(coro):
    """Run an async coroutine from a sync Dramatiq actor."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@dramatiq.actor(max_retries=3, min_backoff=5_000, max_backoff=60_000)
def ingest_document_task(document_id: str) -> None:
    """Parse, chunk, embed, and index a document."""
    logger.info("task.ingest.start", document_id=document_id)
    _run_async(_ingest(document_id))


async def _ingest(document_id: str) -> None:
    from app.containers import Container

    settings = get_settings()
    container = Container(settings=settings)
    await container.init_resources()
    try:
        await container.ingestion_service.run(document_id)
    finally:
        await container.close_resources()


@dramatiq.actor(max_retries=1)
def reindex_document_task(document_id: str) -> None:
    """Re-index a single document (bump version)."""
    logger.info("task.reindex.start", document_id=document_id)
    _run_async(_reindex(document_id))


async def _reindex(document_id: str) -> None:
    from app.containers import Container

    settings = get_settings()
    container = Container(settings=settings)
    await container.init_resources()
    try:
        await container.ingestion_service.run(document_id, reindex=True)
    finally:
        await container.close_resources()


@dramatiq.actor(max_retries=1)
def delete_document_task(document_id: str) -> None:
    """Soft-delete a document and clean up its index entries."""
    logger.info("task.delete.start", document_id=document_id)
    _run_async(_delete(document_id))


async def _delete(document_id: str) -> None:
    from app.containers import Container

    settings = get_settings()
    container = Container(settings=settings)
    await container.init_resources()
    try:
        doc_uuid = uuid.UUID(document_id)
        await container.document_repo.soft_delete(doc_uuid)
        container.chunk_index_repo.delete_by_document(str(doc_uuid))
    finally:
        await container.close_resources()


@dramatiq.actor(max_retries=1)
def reconcile_task() -> None:
    """Run SQL/Chroma consistency check and repair."""
    logger.info("task.reconcile.start")
    _run_async(_reconcile())


async def _reconcile() -> None:
    from app.containers import Container

    settings = get_settings()
    container = Container(settings=settings)
    await container.init_resources()
    try:
        await container.reconcile_service.run()
    finally:
        await container.close_resources()


@dramatiq.actor(max_retries=1)
def cleanup_old_chats_task() -> None:
    """Purge chat logs older than the configured retention period."""
    logger.info("task.cleanup.start")
    _run_async(_cleanup())


async def _cleanup() -> None:
    from app.containers import Container

    settings = get_settings()
    container = Container(settings=settings)
    await container.init_resources()
    try:
        summary = await container.cleanup_service.purge_old_chats()
        logger.info("task.cleanup.done", **summary)
    finally:
        await container.close_resources()
