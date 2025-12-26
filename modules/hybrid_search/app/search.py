"""Hybrid search combining lexical (OpenSearch) and semantic (Qdrant)."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from modules.authority.app.context import AuthorityContext  # type: ignore
from modules.authority.app.engine import AccessDecision, evaluate_document_access  # type: ignore
from modules.authority.app.policy import load_default_context  # type: ignore
from modules.metadata.app.audit import audit_logger  # type: ignore
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
    body = {
        "query": {
            "bool": {
                "must": [{"match": {"content": query}}],
            }
        }
    }
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
        doc_id = payload.get("document_id")
        chunk_id = payload.get("chunk_id") or str(p.id)
        results.append(
            {
                "chunk_id": chunk_id,
                "document_id": doc_id,
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
    if not entry.get("content"):
        entry["content"] = row.get("content")
    if not entry.get("document_id"):
        entry["document_id"] = row.get("document_id")
    if not entry.get("artefact_id"):
        entry["artefact_id"] = row.get("artefact_id")


def _require_value(value: object, label: str) -> None:
    if value is None or value == "":
        raise RuntimeError(f"Missing required field: {label}")


def _explain_match(lexical_score: float, semantic_score: float) -> str:
    if lexical_score > 0 and semantic_score > 0:
        return (
            "Matched lexical and semantic retrieval "
            f"(lexical_score={lexical_score:.6f}, semantic_score={semantic_score:.6f})."
        )
    if lexical_score > 0:
        return f"Matched lexical retrieval (lexical_score={lexical_score:.6f})."
    if semantic_score > 0:
        return f"Matched semantic retrieval (semantic_score={semantic_score:.6f})."
    raise RuntimeError("Missing explanation metadata: no positive match score")


def _explain_allowed(matched_rule_ids: List[int], reasons: List[str]) -> str:
    if not matched_rule_ids:
        raise RuntimeError("Missing explanation metadata: matched_rule_ids empty for ALLOW")
    reason_str = ", ".join(reasons) if reasons else "rule_match"
    return f"Access decision ALLOW via {reason_str}; matched_rule_ids={matched_rule_ids}."


def _explain_ranked(lexical_norm: float, semantic_norm: float, final_score: float) -> str:
    return (
        "Ranked by hybrid score = 0.5*lexical_norm + 0.5*semantic_norm "
        f"({final_score:.6f} = 0.5*{lexical_norm:.6f} + 0.5*{semantic_norm:.6f})."
    )


def _build_response(
    *,
    query_id: str,
    timestamp: str,
    query: str,
    results: List[Dict],
) -> Dict:
    _require_value(query_id, "query_id")
    _require_value(timestamp, "timestamp")
    _require_value(query, "query")
    return {
        "query_id": query_id,
        "timestamp": timestamp,
        "query": query,
        "results": results,
    }


def hybrid_search(
    query: str,
    context: Optional[AuthorityContext] = None,
    top_k: Optional[int] = None,
    *,
    query_id: Optional[str] = None,
) -> Dict:
    """
    Hybrid search with authority enforcement.
    
    Retrieves candidates, evaluates authority per document, and filters denied results.
    """
    ctx = context or load_default_context()
    k = top_k or settings.default_top_k
    qid = query_id or str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    audit_logger.query_received(
        actor=ctx.user,
        query_id=qid,
        context=ctx,
        outcome={"query": query, "top_k": k},
    )
    audit_logger.search_query(actor=ctx.user, query=query, context=ctx, query_id=qid)

    lex = _search_lexical(query, k)
    sem = _search_semantic(query, k)
    audit_logger.search_executed(
        actor=ctx.user,
        query_id=qid,
        context=ctx,
        outcome={"lexical_count": len(lex), "semantic_count": len(sem)},
    )

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
    decisions: Dict[str, AccessDecision] = {}
    denied_count = 0
    for entry in merged.values():
        lexical_norm = entry.get("lexical_norm", 0.0)
        semantic_norm = entry.get("semantic_norm", 0.0)
        final_score = 0.5 * lexical_norm + 0.5 * semantic_norm
        _hydrate_entry(entry)
        doc_id = entry.get("document_id")
        if not doc_id:
            raise RuntimeError("Missing required field: document_id")
        decision = decisions.get(doc_id)
        if decision is None:
            decision = evaluate_document_access(ctx, doc_id, query_id=qid)
            decisions[doc_id] = decision
        if not decision.allowed:
            denied_count += 1
            continue
        if not entry.get("content"):
            raise RuntimeError("Missing required field: snippet source content")
        _require_value(entry.get("chunk_id"), "chunk_id")
        _require_value(entry.get("document_id"), "document_id")
        snippet = (entry.get("content") or "")[:200]
        explanation = {
            "why_matched": _explain_match(
                entry.get("lexical_score", 0.0), entry.get("semantic_score", 0.0)
            ),
            "why_allowed": _explain_allowed(decision.matched_rule_ids, decision.reasons),
            "why_ranked": _explain_ranked(lexical_norm, semantic_norm, final_score),
        }
        results.append(
            {
                "document_id": entry.get("document_id"),
                "chunk_id": entry.get("chunk_id"),
                "snippet": snippet,
                "scores": {
                    "lexical": entry.get("lexical_score", 0.0),
                    "semantic": entry.get("semantic_score", 0.0),
                    "final": final_score,
                },
                "authority": {
                    "decision": "ALLOW",
                    "matched_rule_ids": list(decision.matched_rule_ids),
                },
                "explanation": explanation,
            }
        )

    results.sort(key=lambda x: x["scores"]["final"], reverse=True)
    audit_logger.authority_evaluated(
        actor=ctx.user,
        query_id=qid,
        context=ctx,
        outcome={"evaluated": len(decisions), "denied": denied_count, "allowed": len(results)},
    )
    audit_logger.results_filtered(
        actor=ctx.user,
        query_id=qid,
        context=ctx,
        outcome={"input": len(merged), "returned": len(results)},
    )
    returned_doc_ids = [r.get("document_id") for r in results if r.get("document_id")]
    audit_logger.search_results_returned(
        actor=ctx.user,
        count=len(results),
        document_ids=returned_doc_ids,
        context=ctx,
        query_id=qid,
    )
    audit_logger.response_returned(
        actor=ctx.user,
        query_id=qid,
        context=ctx,
        outcome={"count": len(results)},
    )
    return _build_response(query_id=qid, timestamp=timestamp, query=query, results=results)
