"""Chunking policy — token-based splitting with overlap and page-aware boundaries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChunkingConfig:
    """Tuneable chunking parameters."""

    chunk_size: int = 512
    chunk_overlap: int = 64
    min_chunk_size: int = 50


@dataclass
class TextChunk:
    """A single text chunk produced by the policy."""

    text: str
    page: int
    chunk_index: int


class ChunkingPolicy:
    """Splits text into chunks respecting size, overlap, and page boundaries.

    This is a character-based splitter (not true token-based) because counting
    tokens requires a tokeniser tied to a specific model.  For an embedding model
    with ~4 chars per token, ``chunk_size=512`` chars ≈ 128 tokens.
    """

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self._cfg = config or ChunkingConfig()

    @property
    def config(self) -> ChunkingConfig:
        return self._cfg

    def split_text(self, text: str, *, page: int = 1) -> list[TextChunk]:
        """Split a single page / block of text into overlapping chunks."""
        if not text or not text.strip():
            return []

        chunks: list[TextChunk] = []
        start = 0
        idx = 0
        size = self._cfg.chunk_size
        overlap = self._cfg.chunk_overlap

        while start < len(text):
            end = start + size
            chunk_text = text[start:end].strip()

            if len(chunk_text) >= self._cfg.min_chunk_size:
                chunks.append(TextChunk(text=chunk_text, page=page, chunk_index=idx))
                idx += 1

            if end >= len(text):
                break
            start = end - overlap

        return chunks

    def split_pages(self, pages: dict[int, str]) -> list[TextChunk]:
        """Split multiple pages, keeping chunk_index globally sequential."""
        all_chunks: list[TextChunk] = []
        global_idx = 0
        for page_num in sorted(pages.keys()):
            page_text = pages[page_num]
            page_chunks = self.split_text(page_text, page=page_num)
            for chunk in page_chunks:
                chunk.chunk_index = global_idx
                all_chunks.append(chunk)
                global_idx += 1
        return all_chunks
