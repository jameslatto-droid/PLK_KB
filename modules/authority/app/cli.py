import argparse
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .config import settings
from .context import AuthorityContext
from .engine import evaluate_document_access, get_allowed_document_ids
from .policy import load_default_context, validate_authority_level
from .repository import fetch_documents_with_rules


def _parse_list(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _context_from_args(args: argparse.Namespace) -> AuthorityContext:
    return AuthorityContext(
        user=args.user or settings.actor,
        roles=_parse_list(args.roles) if args.roles is not None else list(settings.default_roles),
        project_codes=_parse_list(args.project_codes) if args.project_codes is not None else list(settings.default_project_codes),
        discipline=args.discipline or settings.default_discipline,
        classification=args.classification if args.classification is not None else settings.default_classification,
        commercial_sensitivity=(
            args.commercial_sensitivity
            if args.commercial_sensitivity is not None
            else settings.default_commercial_sensitivity
        ),
    )


def cmd_validate(args: argparse.Namespace) -> None:
    validate_authority_level(args.authority_level)
    print("authority_level is valid")


def cmd_eval_doc(args: argparse.Namespace) -> None:
    context = _context_from_args(args)
    decision = evaluate_document_access(context, args.document_id)
    status = "ALLOW" if decision.allowed else "DENY"
    print(f"{status} document_id={decision.document_id} reasons={decision.reasons} matched_rule={decision.matched_rule_id}")


def cmd_eval_batch(args: argparse.Namespace) -> None:
    context = _context_from_args(args)
    allowed = get_allowed_document_ids(context)
    for doc_id in sorted(allowed):
        print(doc_id)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Authority evaluation CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Validate authority_level value")
    p_val.add_argument("authority_level")
    p_val.set_defaults(func=cmd_validate)

    p_doc = sub.add_parser("eval-doc", help="Evaluate a single document")
    p_doc.add_argument("document_id")
    _add_context_args(p_doc)
    p_doc.set_defaults(func=cmd_eval_doc)

    p_batch = sub.add_parser("eval-batch", help="Evaluate all documents for allowed set")
    _add_context_args(p_batch)
    p_batch.set_defaults(func=cmd_eval_batch)

    return parser


def _add_context_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--user", default=None)
    p.add_argument("--roles", default=None, help="Comma-separated roles (default from env)")
    p.add_argument("--project-codes", default=None, help="Comma-separated project codes (default from env)")
    p.add_argument("--discipline", default=None, help="Discipline (default from env)")
    p.add_argument("--classification", default=None, help="Classification (default from env)")
    p.add_argument(
        "--commercial-sensitivity", default=None, help="Commercial sensitivity (default from env)"
    )


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
