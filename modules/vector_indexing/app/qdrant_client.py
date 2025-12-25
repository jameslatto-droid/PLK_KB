"""Qdrant client utilities for vector indexing."""

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

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


def recreate_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    vectors_config = qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE)
    client.recreate_collection(collection_name=collection_name, vectors_config=vectors_config)
