"""Lexical indexing pipeline."""

from typing import List, Dict, Any

from .opensearch_client import bulk_index, create_index, delete_index, get_client
from .config import settings

from modules.metadata.app.repository import ChunkRepository  # type: ignore


def _load_all_chunks_with_lineage() -> List[Dict[str, Any]]:
    # Fetch all chunks and resolve document_id via artefact -> version -> document join
    rows = ChunkRepository.list_all_with_lineage()
    return rows


def _to_opensearch_doc(row: Dict[str, Any]) -> Dict[str, Any]:
    meta = row.get("metadata") or {}
    return {
        "chunk_id": row["chunk_id"],
        "artefact_id": row["artefact_id"],
        "document_id": row["document_id"],
        "content": row["content"],
        "chunk_index": meta.get("chunk_index"),
        "char_start": meta.get("char_start"),
        "char_end": meta.get("char_end"),
    }


def index_all_chunks() -> int:
    client = get_client()
    delete_index(client, settings.index_name)
    create_index(client, settings.index_name)

    rows = _load_all_chunks_with_lineage()
    docs = [_to_opensearch_doc(r) for r in rows]
    if docs:
        bulk_index(client, settings.index_name, docs)
    return len(docs)
