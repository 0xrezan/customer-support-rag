from __future__ import annotations

from typing import Any

from app.infrastructure.vectorstore.chroma_client import create_chroma_client


def test_chroma_client_disables_anonymized_telemetry(monkeypatch) -> None:
    calls: dict[str, Any] = {}
    sentinel_client = object()

    def fake_http_client(**kwargs: Any) -> object:
        calls.update(kwargs)
        return sentinel_client

    monkeypatch.setattr("chromadb.HttpClient", fake_http_client)

    client = create_chroma_client(host="localhost", port=18100)

    assert client is sentinel_client
    assert calls["settings"].anonymized_telemetry is False
    assert (
        calls["settings"].chroma_product_telemetry_impl
        == "app.infrastructure.vectorstore.chroma_telemetry.NoopProductTelemetryClient"
    )
    assert (
        calls["settings"].chroma_telemetry_impl
        == "app.infrastructure.vectorstore.chroma_telemetry.NoopProductTelemetryClient"
    )


def test_noop_chroma_telemetry_client_imports_cleanly() -> None:
    from app.infrastructure.vectorstore.chroma_telemetry import NoopProductTelemetryClient

    assert NoopProductTelemetryClient.__name__ == "NoopProductTelemetryClient"
