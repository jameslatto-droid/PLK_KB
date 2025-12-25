"""Authority policy definitions and helpers."""

from dataclasses import dataclass
from typing import List, Optional, Set

from .config import settings
from .context import AuthorityContext

ALLOWED_AUTHORITY_LEVELS: Set[str] = {"AUTHORITATIVE", "DRAFT", "REFERENCE", "EXTERNAL"}


@dataclass(frozen=True)
class AccessRule:
    rule_id: Optional[int]
    project_code: Optional[str]
    discipline: Optional[str]
    classification: Optional[str]
    commercial_sensitivity: Optional[str]
    allowed_roles: List[str]


def validate_authority_level(level: str) -> str:
    normalized = (level or "").upper()
    if normalized not in ALLOWED_AUTHORITY_LEVELS:
        raise ValueError(f"Invalid authority_level: {level}")
    return normalized


def rule_matches(rule: AccessRule, context: AuthorityContext) -> bool:
    matched, _ = rule_match_reason(rule, context)
    return matched


def rule_match_reason(rule: AccessRule, context: AuthorityContext) -> tuple[bool, Optional[str]]:
    if rule.project_code and rule.project_code not in context.project_codes:
        return False, "project_mismatch"
    if rule.discipline and rule.discipline != context.discipline:
        return False, "discipline_mismatch"
    if rule.classification and rule.classification != context.classification:
        return False, "classification_mismatch"
    if rule.commercial_sensitivity and rule.commercial_sensitivity != context.commercial_sensitivity:
        return False, "commercial_sensitivity_mismatch"
    allowed_roles = set(rule.allowed_roles or [])
    if not allowed_roles:
        return False, "allowed_roles_empty"
    if not allowed_roles.intersection(context.roles):
        return False, "role_mismatch"
    return True, None


def load_default_context(user: Optional[str] = None) -> AuthorityContext:
    return AuthorityContext(
        user=user or settings.actor,
        roles=list(settings.default_roles),
        project_codes=list(settings.default_project_codes),
        discipline=settings.default_discipline,
        classification=settings.default_classification,
        commercial_sensitivity=settings.default_commercial_sensitivity,
    )
