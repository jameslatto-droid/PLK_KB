"""
Qdrant client boundary.

At Stage 2, this is a placeholder. No embeddings are generated here.
"""
from app.config import settings


def get_qdrant_endpoint() -> str:
    return f"http://{settings.qdrant_host}:{settings.qdrant_port}"


def ensure_collection(collection_name: str):
    raise NotImplementedError("Qdrant collection management not implemented (Stage 2)")


def upsert_vectors(collection_name: str, points: list[dict]):
    raise NotImplementedError("Qdrant upsert not implemented (Stage 2)")
