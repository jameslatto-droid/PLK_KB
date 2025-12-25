import argparse
import sys
from pathlib import Path

from opensearchpy import OpenSearch

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .config import settings
from .opensearch_client import get_client


def search(query: str, size: int = 5):
    client: OpenSearch = get_client()
    body = {
        "query": {
            "match": {
                "content": query,
            }
        }
    }
    resp = client.search(index=settings.index_name, body=body, size=size)
    hits = resp.get("hits", {}).get("hits", [])
    if not hits:
        print("No results")
        return

    for h in hits:
        source = h.get("_source", {})
        snippet = (source.get("content") or "")[:160]
        print(source.get("chunk_id"), source.get("document_id"), snippet)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search chunks index")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--size", type=int, default=5)
    args = parser.parse_args(argv)

    search(args.query, size=args.size)


if __name__ == "__main__":
    main()
