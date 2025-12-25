"""Authority evaluation logic.

Given an AuthorityContext, returns the set of document_ids that satisfy
both authority-level gating and at least one fully matching access_rule.
"""

from collections import defaultdict
from typing import Dict, List, Set

from .context import AuthorityContext
from .repository import fetch_documents_with_rules

ALLOWED_LEVELS = {"AUTHORITATIVE", "REFERENCE", "DRAFT", "EXTERNAL"}


def get_allowed_document_ids(context: AuthorityContext) -> Set[str]:
    """
    Returns a set of document_ids the context is allowed to see.
    Deterministic, DB-backed, no side effects.
    """
    rows = fetch_documents_with_rules()

    grouped: Dict[str, Dict] = defaultdict(lambda: {"authority_level": None, "rules": []})
    for row in rows:
        doc_id = row.get("document_id")
        if not doc_id:
            continue
        grouped[doc_id]["authority_level"] = row.get("authority_level")
        if row.get("rule_id") is not None:
            grouped[doc_id]["rules"].append(
                {
                    "project_code": row.get("rule_project_code"),
                    "discipline": row.get("discipline"),
                    "classification": row.get("classification"),
                    "allowed_roles": row.get("allowed_roles") or [],
                }
            )

    allowed: Set[str] = set()
    for doc_id, data in grouped.items():
        authority_level = (data.get("authority_level") or "").upper()
        if authority_level not in ALLOWED_LEVELS:
            continue

        rules: List[Dict] = data.get("rules", [])
        if not rules:
            # Explicit deny when no access_rules are present.
            continue

        if any(_rule_matches(rule, context) for rule in rules):
            # AUTHORITATIVE/REFERENCE still require a matching rule; DRAFT/EXTERNAL
            # also require explicit allow.
            allowed.add(doc_id)

    return allowed


def _rule_matches(rule: Dict, context: AuthorityContext) -> bool:
    project_code = rule.get("project_code")
    if project_code and project_code not in context.project_codes:
        return False

    discipline = rule.get("discipline")
    if discipline and discipline != context.discipline:
        return False

    classification = rule.get("classification")
    # Context carries no classification attribute; only unclassified (null/empty)
    # rules can match securely.
    if classification:
        return False

    allowed_roles = set(rule.get("allowed_roles") or [])
    if not allowed_roles:
        return False

    role_overlap = allowed_roles.intersection(context.roles)
    if not role_overlap:
        return False

    return True
