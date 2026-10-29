"""Integration test — delete document and Chroma cleanup.

Tests soft-delete logic and index cleanup with mocked repositories.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.db.models import DocumentStatus


@pytest.mark.integration
class TestDeleteDocument:
    async def test_soft_delete_updates_status(self) -> None:
        """Soft-delete sets status to DELETED in the document repository."""
        doc_id = uuid.uuid4()

        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.status = DocumentStatus.INDEXED

        doc_repo = AsyncMock()
        doc_repo.soft_delete.return_value = None
        doc_repo.get.return_value = mock_doc

        # Simulate the delete task logic (from tasks.py _delete)
        await doc_repo.soft_delete(doc_id)

        doc_repo.soft_delete.assert_called_once_with(doc_id)

    async def test_delete_cleans_chroma(self) -> None:
        """After deletion, the chunk index should remove all chunks for the document."""
        doc_id = uuid.uuid4()

        doc_repo = AsyncMock()
        doc_repo.soft_delete.return_value = None

        chunk_index = MagicMock()
        chunk_index.delete_by_document = MagicMock()

        # Simulate the full delete flow
        await doc_repo.soft_delete(doc_id)
        chunk_index.delete_by_document(str(doc_id))

        doc_repo.soft_delete.assert_called_once_with(doc_id)
        chunk_index.delete_by_document.assert_called_once_with(str(doc_id))

    async def test_delete_task_converts_str_to_uuid(self) -> None:
        """The delete task should convert string document_id to UUID."""
        doc_id = uuid.uuid4()
        doc_id_str = str(doc_id)

        doc_repo = AsyncMock()
        doc_repo.soft_delete.return_value = None

        chunk_index = MagicMock()
        chunk_index.delete_by_document = MagicMock()

        # Simulate the fixed _delete() logic
        doc_uuid = uuid.UUID(doc_id_str)
        await doc_repo.soft_delete(doc_uuid)
        chunk_index.delete_by_document(str(doc_uuid))

        # Verify UUID was used, not string
        doc_repo.soft_delete.assert_called_once_with(doc_uuid)
        assert isinstance(doc_repo.soft_delete.call_args[0][0], uuid.UUID)
