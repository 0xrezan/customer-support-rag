"""No-op Chroma telemetry adapter used to keep local runtime logs quiet."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chromadb.telemetry.product import ProductTelemetryClient, ProductTelemetryEvent
from overrides import override

if TYPE_CHECKING:
    from chromadb.config import System


class NoopProductTelemetryClient(ProductTelemetryClient):
    """Drop Chroma product telemetry events."""

    def __init__(self, system: System) -> None:
        super().__init__(system)

    @override
    def capture(self, event: ProductTelemetryEvent) -> None:
        return None
