"""Dedupe and idempotency tests — content hash and question dedupe."""

from __future__ import annotations

import uuid

from app.utils.hashing import content_hash, question_hash
from app.utils.ids import deterministic_uuid, make_chunk_id


class TestContentHash:
    def test_same_bytes_produce_same_hash(self) -> None:
        data = b"Hello, world!"
        assert content_hash(data) == content_hash(data)

    def test_different_bytes_produce_different_hash(self) -> None:
        assert content_hash(b"Hello") != content_hash(b"World")

    def test_hash_is_sha256_hex(self) -> None:
        h = content_hash(b"test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestQuestionHash:
    def test_same_text_produces_same_hash(self) -> None:
        assert question_hash("What is your policy?") == question_hash("What is your policy?")

    def test_normalisation_makes_equivalent_texts_match(self) -> None:
        # Extra spaces and different casing should normalise to same hash
        assert question_hash("What  is  your  POLICY?") == question_hash("what is your policy?")

    def test_different_questions_produce_different_hash(self) -> None:
        assert question_hash("Question A") != question_hash("Question B")


class TestChunkId:
    def test_deterministic(self) -> None:
        doc_id = uuid.UUID("12345678-1234-1234-1234-123456789012")
        id1 = make_chunk_id(doc_id, version=1, page=2, chunk_index=3)
        id2 = make_chunk_id(doc_id, version=1, page=2, chunk_index=3)
        assert id1 == id2

    def test_different_inputs_produce_different_ids(self) -> None:
        doc_id = uuid.UUID("12345678-1234-1234-1234-123456789012")
        id1 = make_chunk_id(doc_id, version=1, page=1, chunk_index=0)
        id2 = make_chunk_id(doc_id, version=1, page=1, chunk_index=1)
        assert id1 != id2

    def test_format(self) -> None:
        doc_id = uuid.UUID("12345678-1234-1234-1234-123456789012")
        chunk_id = make_chunk_id(doc_id, version=2, page=3, chunk_index=4)
        assert chunk_id == "12345678-1234-1234-1234-123456789012:2:3:4"


class TestDeterministicUUID:
    def test_same_seed_same_uuid(self) -> None:
        assert deterministic_uuid("seed") == deterministic_uuid("seed")

    def test_different_seed_different_uuid(self) -> None:
        assert deterministic_uuid("a") != deterministic_uuid("b")
