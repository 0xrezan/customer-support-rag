"""SQLAlchemy declarative base for all ORM models."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(DeclarativeBase, MappedAsDataclass):
    """Base class used by all SQLAlchemy mapped models.

    Uses ``MappedAsDataclass`` so every model gets ``__init__``, ``__repr__``,
    and ``__eq__`` for free while staying fully compatible with ``Mapped[]``
    type annotations.
    """
