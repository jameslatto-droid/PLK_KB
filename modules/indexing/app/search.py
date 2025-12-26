import argparse
import sys
from pathlib import Path
from typing import List
from uuid import uuid4

from opensearchpy import OpenSearch

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.authority.app.context import AuthorityContext  # type: ignore
from modules.authority.app.engine import get_allowed_document_ids  # type: ignore
from modules.authority.app.policy import load_default_context  # type: ignore
from modules.metadata.app.audit import audit_logger  # type: ignore
from .config import settings
from .opensearch_client import get_client


def _parse_list(raw: str) -> List[str]:
    return [v.strip() for v in raw.split(",") if v.strip()]


def search(query: str, *, size: int = 5, context: AuthorityContext | None = None):
    ctx = context or load_default_context()
    query_id = str(uuid4())
    audit_logger.search_query(actor=ctx.user, query=query, context=ctx, query_id=query_id)

    allowed_doc_ids = get_allowed_document_ids(ctx, query_id=query_id)
    if not allowed_doc_ids:
        print("No results (unauthorized)")
        audit_logger.search_results_returned(
            actor=ctx.user,
            count=0,
            document_ids=[],
            context=ctx,
            query_id=query_id,
        )
        return

    client: OpenSearch = get_client()
    body = {
        "query": {
            "bool": {
                "must": {"match": {"content": query}},
                "filter": [{"terms": {"document_id": list(allowed_doc_ids)}}],
            }
        }
    }
    resp = client.search(index=settings.index_name, body=body, size=size)
    hits = resp.get("hits", {}).get("hits", [])
    if not hits:
        print("No results")
        audit_logger.search_results_returned(
            actor=ctx.user,
            count=0,
            document_ids=[],
            context=ctx,
            query_id=query_id,
        )
        return

    returned_doc_ids = []
    for h in hits:
        source = h.get("_source", {})
        snippet = (source.get("content") or "")[:160]
        doc_id = source.get("document_id")
        if doc_id:
            returned_doc_ids.append(doc_id)
        print(source.get("chunk_id"), doc_id, snippet)

    audit_logger.search_results_returned(
        actor=ctx.user,
        count=len(hits),
        document_ids=returned_doc_ids,
        context=ctx,
        query_id=query_id,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search chunks index")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--size", type=int, default=5)
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

    search(args.query, size=args.size, context=context)


if __name__ == "__main__":
    main()
