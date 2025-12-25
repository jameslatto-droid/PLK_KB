import argparse
import sys
from pathlib import Path
from typing import List

from qdrant_client.http import models as qmodels

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .config import settings
from .embeddings import embed_text
from .qdrant_client import get_client


def search(query: str, limit: int | None = None) -> None:
    client = get_client()
    vector = embed_text(query)
    top_k = limit or settings.search_top_k

    response = client.query_points(
        collection_name=settings.collection_name,
        query=vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )

    results: List[qmodels.ScoredPoint] = getattr(response, "points", [])

    if not results:
        print("No results")
        return

    for r in results:
        payload = r.payload or {}
        doc_id = payload.get("document_id")
        chunk_index = payload.get("chunk_index")
        span = f"{payload.get('char_start')}-{payload.get('char_end')}"
        print(f"{r.id} doc={doc_id} chunk={chunk_index} span={span} score={r.score:.4f}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Semantic search over chunks")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--size", type=int, default=None, help="Number of results (default from settings)")
    args = parser.parse_args(argv)

    search(args.query, limit=args.size)


if __name__ == "__main__":
    main()
