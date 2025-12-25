"""Hybrid search combining lexical (OpenSearch) and semantic (Qdrant)."""

from typing import Dict, List, Optional

from modules.vector_indexing.app.embeddings import embed_text  # type: ignore
from opensearchpy import OpenSearch
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from .config import settings
from .opensearch_client import get_client as get_os_client
from .qdrant_client import get_client as get_qdrant_client
from .repository import get_chunk_with_document


def _normalize_scores(items: List[Dict], key: str) -> None:
    max_score = max((item.get(key) or 0.0) for item in items) if items else 0.0
    if max_score <= 0:
        for item in items:
            item[f"normalized_{key}"] = 0.0
        return
    for item in items:
        item[f"normalized_{key}"] = (item.get(key) or 0.0) / max_score


def _search_lexical(query: str, top_k: int) -> List[Dict]:
    client: OpenSearch = get_os_client()
    body = {"query": {"match": {"content": query}}}
    resp = client.search(index=settings.opensearch_index, body=body, size=top_k)
    hits = resp.get("hits", {}).get("hits", [])
    results: List[Dict] = []
    for h in hits:
        src = h.get("_source", {})
        results.append(
            {
                "chunk_id": src.get("chunk_id"),
                "document_id": src.get("document_id"),
                "artefact_id": src.get("artefact_id"),
                "content": src.get("content"),
                "lexical_score": h.get("_score", 0.0),
            }
        )
    _normalize_scores(results, "lexical_score")
    return results


def _search_semantic(query: str, top_k: int) -> List[Dict]:
    client: QdrantClient = get_qdrant_client()
    vector = embed_text(query)

    response = client.query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )
    points: List[qmodels.ScoredPoint] = getattr(response, "points", [])

    results: List[Dict] = []
    for p in points:
        payload = p.payload or {}
        chunk_id = payload.get("chunk_id") or str(p.id)
        results.append(
            {
                "chunk_id": chunk_id,
                "document_id": payload.get("document_id"),
                "artefact_id": payload.get("artefact_id"),
                "semantic_score": p.score or 0.0,
            }
        )
    _normalize_scores(results, "semantic_score")
    return results


def _hydrate_entry(entry: Dict) -> None:
    """Fill missing content/document/artefact from metadata DB."""
    if entry.get("content") and entry.get("document_id") and entry.get("artefact_id"):
        return
    row = get_chunk_with_document(entry["chunk_id"])
    if not row:
        return
    entry.setdefault("content", row.get("content"))
    entry.setdefault("document_id", row.get("document_id"))
    entry.setdefault("artefact_id", row.get("artefact_id"))


def hybrid_search(query: str, top_k: Optional[int] = None) -> List[Dict]:
    k = top_k or settings.default_top_k
    lex = _search_lexical(query, k)
    sem = _search_semantic(query, k)

    merged: Dict[str, Dict] = {}
    for item in lex:
        merged[item["chunk_id"]] = {
            "chunk_id": item["chunk_id"],
            "document_id": item.get("document_id"),
            "artefact_id": item.get("artefact_id"),
            "lexical_score": item.get("lexical_score", 0.0),
            "semantic_score": 0.0,
            "content": item.get("content"),
            "semantic_norm": 0.0,
            "lexical_norm": item.get("normalized_lexical_score", 0.0),
        }

    for item in sem:
        entry = merged.get(item["chunk_id"])
        if entry:
            entry["semantic_score"] = item.get("semantic_score", 0.0)
            entry["semantic_norm"] = item.get("normalized_semantic_score", 0.0)
            entry["lexical_norm"] = entry.get("lexical_norm", 0.0)
        else:
            merged[item["chunk_id"]] = {
                "chunk_id": item["chunk_id"],
                "document_id": item.get("document_id"),
                "artefact_id": item.get("artefact_id"),
                "lexical_score": 0.0,
                "semantic_score": item.get("semantic_score", 0.0),
                "content": None,
                "semantic_norm": item.get("normalized_semantic_score", 0.0),
                "lexical_norm": 0.0,
            }

    results: List[Dict] = []
    for entry in merged.values():
        lexical_norm = entry.get("lexical_norm", 0.0)
        semantic_norm = entry.get("semantic_norm", 0.0)
        final_score = 0.5 * lexical_norm + 0.5 * semantic_norm
        _hydrate_entry(entry)
        snippet = (entry.get("content") or "")[:200]
        results.append(
            {
                "chunk_id": entry["chunk_id"],
                "document_id": entry.get("document_id"),
                "artefact_id": entry.get("artefact_id"),
                "lexical_score": entry.get("lexical_score", 0.0),
                "semantic_score": entry.get("semantic_score", 0.0),
                "final_score": final_score,
                "snippet": snippet,
            }
        )

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results
