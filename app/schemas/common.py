"""Shared response envelope models."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    ok: bool = True
    data: T | None = None
    error: str | None = None


class ErrorResponse(BaseModel):
    ok: bool = False
    error: str
    detail: str | None = None
