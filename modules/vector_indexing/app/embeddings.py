"""Embedding utilities for semantic indexing."""

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from .config import settings


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    """Load and cache the sentence transformer model."""
    return SentenceTransformer(settings.embedding_model)


def get_model() -> SentenceTransformer:
    return _load_model()


def get_embedding_dimension() -> int:
    model = get_model()
    return int(model.get_sentence_embedding_dimension())


def embed_text(text: str) -> List[float]:
    model = get_model()
    vector = model.encode(text or "", normalize_embeddings=True)
    return vector.tolist()
