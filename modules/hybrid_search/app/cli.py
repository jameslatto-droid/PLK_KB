import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.authority.app.context import AuthorityContext  # type: ignore
from .config import settings
from .search import hybrid_search


def main(argv=None):
    parser = argparse.ArgumentParser(description="Hybrid lexical + semantic search with authority")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--user", default="anonymous", help="User identifier")
    parser.add_argument("--roles", default="viewer", help="Comma-separated roles")
    parser.add_argument("--projects", default="", help="Comma-separated project codes")
    parser.add_argument("--discipline", default="general", help="User discipline")
    parser.add_argument("--size", type=int, default=None, help="Number of results (default 10)")
    args = parser.parse_args(argv)

    context = AuthorityContext(
        user=args.user,
        roles=[r.strip() for r in args.roles.split(",") if r.strip()],
        project_codes=[p.strip() for p in args.projects.split(",") if p.strip()],
        discipline=args.discipline,
    )

    results = hybrid_search(args.query, context, top_k=args.size or settings.default_top_k)
    if not results:
        print("No results")
        return

    for r in results:
        print(
            f"{r['chunk_id']} doc={r['document_id']} final={r['final_score']:.4f} "
            f"lex={r['lexical_score']:.4f} sem={r['semantic_score']:.4f} snippet={r['snippet']}"
        )


if __name__ == "__main__":
    main()
