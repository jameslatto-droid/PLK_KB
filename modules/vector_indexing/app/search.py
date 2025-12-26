import argparse
import sys
from pathlib import Path
from typing import List
from uuid import uuid4

from qdrant_client.http import models as qmodels

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.authority.app.context import AuthorityContext  # type: ignore
from modules.authority.app.engine import get_allowed_document_ids  # type: ignore
from modules.authority.app.policy import load_default_context  # type: ignore
from modules.metadata.app.audit import audit_logger  # type: ignore
from .config import settings
from .embeddings import embed_text
from .qdrant_client import get_client


def _parse_list(raw: str) -> List[str]:
    return [v.strip() for v in raw.split(",") if v.strip()]


def search(query: str, limit: int | None = None, *, context: AuthorityContext | None = None) -> None:
    ctx = context or load_default_context()
    query_id = str(uuid4())
    audit_logger.search_query(actor=ctx.user, query=query, context=ctx, query_id=query_id)

    allowed_doc_ids = get_allowed_document_ids(ctx, query_id=query_id)
    if not allowed_doc_ids:
        print("No results (unauthorized)")
        audit_logger.search_results_returned(
            actor=ctx.user, count=0, document_ids=[], context=ctx, query_id=query_id
        )
        return

    client = get_client()
    vector = embed_text(query)
    top_k = limit or settings.search_top_k

    response = client.query_points(
        collection_name=settings.collection_name,
        query=vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
        query_filter={
            "must": [
                {
                    "key": "document_id",
                    "match": {"any": list(allowed_doc_ids)},
                }
            ]
        },
    )

    results: List[qmodels.ScoredPoint] = getattr(response, "points", [])

    if not results:
        print("No results")
        audit_logger.search_results_returned(
            actor=ctx.user, count=0, document_ids=[], context=ctx, query_id=query_id
        )
        return

    returned_doc_ids = []
    for r in results:
        payload = r.payload or {}
        doc_id = payload.get("document_id")
        if doc_id:
            returned_doc_ids.append(doc_id)
        chunk_index = payload.get("chunk_index")
        span = f"{payload.get('char_start')}-{payload.get('char_end')}"
        print(f"{r.id} doc={doc_id} chunk={chunk_index} span={span} score={r.score:.4f}")

    audit_logger.search_results_returned(
        actor=ctx.user,
        count=len(results),
        document_ids=returned_doc_ids,
        context=ctx,
        query_id=query_id,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Semantic search over chunks")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--size", type=int, default=None, help="Number of results (default from settings)")
    parser.add_argument("--user", default=None)
    parser.add_argument("--roles", default=None)
    parser.add_argument("--projects", default=None)
    parser.add_argument("--discipline", default=None)
    parser.add_argument("--classification", default=None)
    parser.add_argument("--commercial-sensitivity", default=None)
    args = parser.parse_args(argv)

    default_ctx = load_default_context(user=args.user)
    context = AuthorityContext(
        user=args.user or default_ctx.user,
        roles=_parse_list(args.roles) if args.roles else default_ctx.roles,
        project_codes=_parse_list(args.projects) if args.projects else default_ctx.project_codes,
        discipline=args.discipline or default_ctx.discipline,
        classification=args.classification if args.classification is not None else default_ctx.classification,
        commercial_sensitivity=(
            args.commercial_sensitivity
            if args.commercial_sensitivity is not None
            else default_ctx.commercial_sensitivity
        ),
    )

    search(args.query, limit=args.size, context=context)


if __name__ == "__main__":
    main()
