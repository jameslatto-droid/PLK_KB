"""Authority evaluation engine with audit logging hooks."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from modules.metadata.app.audit import audit_logger  # type: ignore

from .context import AuthorityContext
from .policy import ALLOWED_AUTHORITY_LEVELS, AccessRule, rule_match_reason
from .repository import fetch_documents_with_rules


@dataclass(frozen=True)
class AccessDecision:
    document_id: str
    allowed: bool
    reasons: List[str] = field(default_factory=list)
    matched_rule_id: Optional[int] = None


def _group_rows(rows: List[Dict]) -> Dict[str, Dict]:
    grouped: Dict[str, Dict] = defaultdict(lambda: {"authority_level": None, "rules": []})
    for row in rows:
        doc_id = row.get("document_id")
        if not doc_id:
            continue
        grouped[doc_id]["authority_level"] = row.get("authority_level")
        if row.get("rule_id") is not None:
            grouped[doc_id]["rules"].append(
                AccessRule(
                    rule_id=row.get("rule_id"),
                    project_code=row.get("rule_project_code"),
                    discipline=row.get("discipline"),
                    classification=row.get("classification"),
                    commercial_sensitivity=row.get("commercial_sensitivity"),
                    allowed_roles=row.get("allowed_roles") or [],
                )
            )
    return grouped


def evaluate_document_access(context: AuthorityContext, document_id: str) -> AccessDecision:
    grouped = _group_rows(fetch_documents_with_rules([document_id]))
    decision = _evaluate_grouped_document(context, document_id, grouped)
    if decision.allowed:
        audit_logger.authz_allow(context=context, decision=decision)
    else:
        audit_logger.authz_deny(context=context, decision=decision)
    return decision


def _evaluate_grouped_document(
    context: AuthorityContext, document_id: str, grouped: Dict[str, Dict]
) -> AccessDecision:
    data = grouped.get(document_id)
    if not data:
        return AccessDecision(document_id=document_id, allowed=False, reasons=["document_not_found"])

    authority_level = (data.get("authority_level") or "").upper()
    if authority_level not in ALLOWED_AUTHORITY_LEVELS:
        return AccessDecision(document_id=document_id, allowed=False, reasons=["unknown_authority"])

    rules: List[AccessRule] = data.get("rules", [])
    if not rules:
        return AccessDecision(document_id=document_id, allowed=False, reasons=["no_access_rules"])

    failure_reasons: List[str] = []
    for rule in rules:
        matched, reason = rule_match_reason(rule, context)
        if matched:
            return AccessDecision(
                document_id=document_id, allowed=True, matched_rule_id=rule.rule_id
            )
        if reason:
            failure_reasons.append(f"rule_{rule.rule_id}:{reason}")

    reasons = failure_reasons or ["no_rule_match"]
    return AccessDecision(document_id=document_id, allowed=False, reasons=reasons)


def get_allowed_document_ids(context: AuthorityContext) -> Set[str]:
    grouped = _group_rows(fetch_documents_with_rules())
    allowed: Set[str] = set()
    for doc_id in grouped.keys():
        decision = _evaluate_grouped_document(context, doc_id, grouped)
        if decision.allowed:
            audit_logger.authz_allow(context=context, decision=decision)
            allowed.add(doc_id)
        else:
            audit_logger.authz_deny(context=context, decision=decision)
    return allowed
