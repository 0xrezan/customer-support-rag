"""Optional tracing hooks (placeholder for Phase 2 OpenTelemetry integration)."""

from __future__ import annotations


def trace_span(name: str):
    """No-op tracing decorator for Phase 1."""

    def decorator(func):
        return func

    return decorator
