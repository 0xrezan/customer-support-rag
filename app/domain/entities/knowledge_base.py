"""Knowledge base and active version entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from datetime import datetime


@dataclass
class KnowledgeBase:
    """Logical grouping of documents (future multi-tenant support)."""

    id: uuid.UUID
    name: str
    description: str = ""
    active_version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
