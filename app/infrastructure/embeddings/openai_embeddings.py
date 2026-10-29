"""Batched OpenAI embeddings client with retries and timeouts."""

from __future__ import annotations

import openai

from app.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_BATCH_SIZE = 64


class OpenAIEmbeddingClient:
    """Thin adapter around the OpenAI embeddings API."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> None:
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size

    async def embed(self, text: str) -> list[float]:
        """Embed a single text string."""
        response = await self._client.embeddings.create(
            input=[text],
            model=self._model,
            dimensions=self._dimensions,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts in batches."""
        all_embeddings: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            response = await self._client.embeddings.create(
                input=batch,
                model=self._model,
                dimensions=self._dimensions,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            logger.debug(
                "embeddings.batch_done",
                batch_start=start,
                batch_size=len(batch),
            )
        return all_embeddings
