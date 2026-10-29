"""Chunking policy tests — chunk sizes, overlap, and page handling."""

from __future__ import annotations

from app.domain.policies.chunking_policy import ChunkingConfig, ChunkingPolicy


class TestChunkingPolicy:
    def test_empty_text_returns_no_chunks(self, chunking_policy: ChunkingPolicy) -> None:
        assert chunking_policy.split_text("") == []
        assert chunking_policy.split_text("   ") == []

    def test_short_text_returns_single_chunk(self, chunking_policy: ChunkingPolicy) -> None:
        text = "Hello, this is a short text."
        chunks = chunking_policy.split_text(text, page=1)
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].page == 1
        assert chunks[0].chunk_index == 0

    def test_long_text_splits_with_overlap(self) -> None:
        policy = ChunkingPolicy(ChunkingConfig(chunk_size=50, chunk_overlap=10, min_chunk_size=5))
        text = "A" * 120
        chunks = policy.split_text(text, page=3)
        assert len(chunks) >= 2
        assert all(c.page == 3 for c in chunks)
        # Check indices are sequential
        for i, c in enumerate(chunks):
            assert c.chunk_index == i

    def test_overlap_content(self) -> None:
        policy = ChunkingPolicy(ChunkingConfig(chunk_size=50, chunk_overlap=10, min_chunk_size=5))
        text = "ABCDE" * 30  # 150 chars
        chunks = policy.split_text(text)
        if len(chunks) >= 2:
            # The end of chunk 0 should overlap with the beginning of chunk 1
            end_of_first = chunks[0].text[-10:]
            start_of_second = chunks[1].text[:10]
            assert end_of_first == start_of_second

    def test_split_pages_sequential_indices(self, chunking_policy: ChunkingPolicy) -> None:
        pages = {
            1: "Page one content that is long enough to produce chunks." * 3,
            2: "Page two content that is also long enough." * 3,
        }
        chunks = chunking_policy.split_pages(pages)
        assert len(chunks) > 0
        # Indices should be globally sequential
        for i, c in enumerate(chunks):
            assert c.chunk_index == i

    def test_min_chunk_size_filter(self) -> None:
        policy = ChunkingPolicy(
            ChunkingConfig(chunk_size=100, chunk_overlap=10, min_chunk_size=50)
        )
        text = "Short"
        chunks = policy.split_text(text)
        assert len(chunks) == 0
