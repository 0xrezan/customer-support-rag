"""Rebuild index for all active documents."""

from __future__ import annotations

import asyncio

from app.config import get_settings
from app.containers import Container
from app.logging import get_logger, setup_logging

logger = get_logger(__name__)


async def main() -> None:
    settings = get_settings()
    setup_logging(log_level=settings.log_level)

    container = Container(settings=settings)
    await container.init_resources()

    try:
        docs = await container.document_repo.list_active()
        logger.info("reindex_all.start", count=len(docs))

        for doc in docs:
            logger.info("reindex_all.document", doc_id=str(doc.id), filename=doc.filename)
            await container.ingestion_service.run(str(doc.id), reindex=True)

        logger.info("reindex_all.complete", count=len(docs))
    finally:
        await container.close_resources()


if __name__ == "__main__":
    asyncio.run(main())
