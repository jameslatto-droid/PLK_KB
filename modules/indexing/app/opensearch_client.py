"""
OpenSearch client boundary.

At Stage 2, this is a placeholder to prevent accidental logic creep.
"""
from app.config import settings


def get_opensearch_endpoint() -> str:
    return f"http://{settings.opensearch_host}:{settings.opensearch_port}"


def ensure_index(index_name: str):
    raise NotImplementedError("OpenSearch index management not implemented (Stage 2)")


def index_documents(index_name: str, docs: list[dict]):
    raise NotImplementedError("OpenSearch indexing not implemented (Stage 2)")
