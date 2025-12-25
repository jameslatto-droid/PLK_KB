"""Vector indexing pipeline using Qdrant."""

import uuid
from typing import Any, Dict, Iterable, List

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from modules.metadata.app.repository import ChunkRepository  # type: ignore

from .config import settings
from .embeddings import embed_text, get_embedding_dimension
from .qdrant_client import get_client, recreate_collection

BATCH_SIZE = 64


def _batched(items: Iterable[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    batch: List[Dict[str, Any]] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def _to_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    meta = row.get("metadata") or {}
    return {
        "chunk_id": row["chunk_id"],
        "artefact_id": row["artefact_id"],
        "document_id": row["document_id"],
        "chunk_index": meta.get("chunk_index"),
        "char_start": meta.get("char_start"),
        "char_end": meta.get("char_end"),
    }


def _to_point(row: Dict[str, Any]) -> qmodels.PointStruct:
    payload = _to_payload(row)
    vector = embed_text(row.get("content") or "")
    point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, row["chunk_id"]))
    return qmodels.PointStruct(
        id=point_id,
        vector=vector,
        payload=payload,
    )


def index_all_chunks() -> int:
    client: QdrantClient = get_client()
    vector_size = get_embedding_dimension()
    recreate_collection(client, settings.collection_name, vector_size)

    rows = ChunkRepository.list_all_with_lineage()
    total = 0
    for batch in _batched(rows, BATCH_SIZE):
        points = [_to_point(r) for r in batch]
        if points:
            client.upsert(collection_name=settings.collection_name, points=points, wait=True)
            total += len(points)
    return total
