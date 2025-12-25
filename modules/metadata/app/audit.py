"""Audit logging helper with non-blocking inserts."""

import os
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

from dotenv import load_dotenv
from psycopg2.extras import Json

from . import models
from .repository import AuditLogRepository

_ENV_PATH = Path(__file__).resolve().parents[3] / "env" / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

_DEFAULT_ACTOR = os.getenv("PLK_ACTOR", "local_user")


def _context_summary(context: Any) -> dict:
    return {
        "user": getattr(context, "user", None),
        "roles": list(getattr(context, "roles", []) or []),
        "project_codes": list(getattr(context, "project_codes", []) or []),
        "discipline": getattr(context, "discipline", None),
        "classification": getattr(context, "classification", None),
        "commercial_sensitivity": getattr(context, "commercial_sensitivity", None),
    }


def _safe_insert(event: models.AuditLog) -> None:
    try:
        AuditLogRepository.insert_event(event)
    except Exception as exc:  # noqa: BLE001 - best-effort logging only
        print(f"[audit] failed to insert audit event: {exc}", file=sys.stderr)


class AuditLogger:
    def __init__(self, actor: Optional[str] = None):
        self.actor = actor or _DEFAULT_ACTOR

    def authz_allow(self, *, context: Any, decision: Any) -> None:
        event = models.AuditLog(
            actor=getattr(context, "user", None) or self.actor,
            action="AUTHZ_ALLOW",
            document_id=getattr(decision, "document_id", None),
            details={
                "context": _context_summary(context),
                "matched_rule_id": getattr(decision, "matched_rule_id", None),
            },
        )
        _safe_insert(event)

    def authz_deny(self, *, context: Any, decision: Any) -> None:
        event = models.AuditLog(
            actor=getattr(context, "user", None) or self.actor,
            action="AUTHZ_DENY",
            document_id=getattr(decision, "document_id", None),
            details={
                "context": _context_summary(context),
                "reasons": list(getattr(decision, "reasons", []) or []),
            },
        )
        _safe_insert(event)

    def search_query(self, *, actor: Optional[str], query: str, context: Any) -> None:
        event = models.AuditLog(
            actor=actor or self.actor,
            action="SEARCH_QUERY",
            details={
                "query": query,
                "context": _context_summary(context),
            },
        )
        _safe_insert(event)

    def search_results_returned(
        self,
        *,
        actor: Optional[str],
        count: int,
        document_ids: Iterable[str],
        context: Any,
    ) -> None:
        event = models.AuditLog(
            actor=actor or self.actor,
            action="SEARCH_RESULTS_RETURNED",
            details={
                "result_count": count,
                "document_ids": list(document_ids),
                "context": _context_summary(context),
            },
        )
        _safe_insert(event)


audit_logger = AuditLogger()
