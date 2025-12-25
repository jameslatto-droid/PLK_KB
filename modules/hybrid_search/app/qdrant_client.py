"""Qdrant client utilities for hybrid search."""

from qdrant_client import QdrantClient

from .config import settings


def get_client() -> QdrantClient:
    client = QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        https=False,
        api_key=settings.qdrant_api_key,
    )
    try:
        client.get_collections()
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError("Qdrant connection failed") from exc
    return client
