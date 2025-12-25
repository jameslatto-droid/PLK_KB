import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.authority.app.context import AuthorityContext  # type: ignore
from modules.authority.app.policy import load_default_context  # type: ignore
from .config import settings
from .search import hybrid_search


def main(argv=None):
    parser = argparse.ArgumentParser(description="Hybrid lexical + semantic search with authority")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--user", default=None, help="User identifier (default from env)")
    parser.add_argument("--roles", default=None, help="Comma-separated roles (default from env)")
    parser.add_argument("--projects", default=None, help="Comma-separated project codes (default from env)")
    parser.add_argument("--discipline", default=None, help="User discipline (default from env)")
    parser.add_argument("--classification", default=None, help="Classification (default from env)")
    parser.add_argument("--commercial-sensitivity", default=None, help="Commercial sensitivity (default from env)")
    parser.add_argument("--size", type=int, default=None, help="Number of results (default 10)")
    args = parser.parse_args(argv)

    default_ctx = load_default_context(user=args.user)
    roles = [r.strip() for r in args.roles.split(",")] if args.roles else default_ctx.roles
    projects = [p.strip() for p in args.projects.split(",") if p.strip()] if args.projects else default_ctx.project_codes
    context = AuthorityContext(
        user=args.user or default_ctx.user,
        roles=[r for r in roles if r],
        project_codes=projects,
        discipline=args.discipline or default_ctx.discipline,
        classification=args.classification if args.classification is not None else default_ctx.classification,
        commercial_sensitivity=(
            args.commercial_sensitivity
            if args.commercial_sensitivity is not None
            else default_ctx.commercial_sensitivity
        ),
    )

    results = hybrid_search(args.query, context=context, top_k=args.size or settings.default_top_k)
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
