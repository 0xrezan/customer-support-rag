"""Re-embed documents after embedding model changes."""

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
        logger.info("backfill.start", count=len(docs))

        for doc in docs:
            logger.info("backfill.document", doc_id=str(doc.id), filename=doc.filename)
            # Delete old index entries and re-ingest
            container.chunk_index_repo.delete_by_document(str(doc.id))
            await container.ingestion_service.run(str(doc.id), reindex=True)

        logger.info("backfill.complete", count=len(docs))
    finally:
        await container.close_resources()


if __name__ == "__main__":
    asyncio.run(main())
