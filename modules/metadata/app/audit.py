"""Audit logging helper with strict inserts."""

import os
import sys
from datetime import datetime, timezone
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


def _event_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_query_id(query_id: Optional[str]) -> str:
    if not query_id:
        raise AuditLogError("missing query_id")
    return query_id


class AuditLogError(RuntimeError):
    pass


def _insert_or_raise(event: models.AuditLog) -> None:
    try:
        AuditLogRepository.insert_event(event)
    except Exception as exc:  # noqa: BLE001 - raise for fail-closed audit
        print(f"[audit] failed to insert audit event: {exc}", file=sys.stderr)
        raise AuditLogError("audit logging failed") from exc


class AuditLogger:
    def __init__(self, actor: Optional[str] = None):
        self.actor = actor or _DEFAULT_ACTOR

    def _log_event(
        self,
        *,
        action: str,
        actor: Optional[str],
        query_id: Optional[str],
        context: Any,
        outcome: object,
        details: Optional[dict] = None,
    ) -> None:
        event_details = {
            "query_id": _require_query_id(query_id),
            "timestamp": _event_timestamp(),
            "outcome": outcome,
            "context": _context_summary(context),
        }
        if details:
            event_details.update(details)
        event = models.AuditLog(
            actor=actor or self.actor,
            action=action,
            details=event_details,
        )
        _insert_or_raise(event)

    def authz_allow(self, *, context: Any, decision: Any, query_id: Optional[str]) -> None:
        event = models.AuditLog(
            actor=getattr(context, "user", None) or self.actor,
            action="AUTHZ_ALLOW",
            document_id=getattr(decision, "document_id", None),
            details={
                "query_id": _require_query_id(query_id),
                "timestamp": _event_timestamp(),
                "context": _context_summary(context),
                "decision": {
                    "decision": "ALLOW",
                    "reasons": list(getattr(decision, "reasons", []) or []),
                    "matched_rule_ids": list(getattr(decision, "matched_rule_ids", []) or []),
                },
            },
        )
        _insert_or_raise(event)

    def authz_deny(self, *, context: Any, decision: Any, query_id: Optional[str]) -> None:
        event = models.AuditLog(
            actor=getattr(context, "user", None) or self.actor,
            action="AUTHZ_DENY",
            document_id=getattr(decision, "document_id", None),
            details={
                "query_id": _require_query_id(query_id),
                "timestamp": _event_timestamp(),
                "context": _context_summary(context),
                "decision": {
                    "decision": "DENY",
                    "reasons": list(getattr(decision, "reasons", []) or []),
                    "matched_rule_ids": list(getattr(decision, "matched_rule_ids", []) or []),
                },
            },
        )
        _insert_or_raise(event)

    def search_query(
        self,
        *,
        actor: Optional[str],
        query: str,
        context: Any,
        query_id: Optional[str],
    ) -> None:
        event = models.AuditLog(
            actor=actor or self.actor,
            action="SEARCH_QUERY",
            details={
                "query_id": _require_query_id(query_id),
                "timestamp": _event_timestamp(),
                "query": query,
                "context": _context_summary(context),
            },
        )
        _insert_or_raise(event)

    def search_results_returned(
        self,
        *,
        actor: Optional[str],
        count: int,
        document_ids: Iterable[str],
        context: Any,
        query_id: Optional[str],
    ) -> None:
        event = models.AuditLog(
            actor=actor or self.actor,
            action="SEARCH_RESULTS_RETURNED",
            details={
                "query_id": _require_query_id(query_id),
                "timestamp": _event_timestamp(),
                "result_count": count,
                "document_ids": list(document_ids),
                "context": _context_summary(context),
            },
        )
        _insert_or_raise(event)

    def query_received(self, *, actor: Optional[str], query_id: Optional[str], context: Any, outcome: object) -> None:
        self._log_event(
            action="QUERY_RECEIVED",
            actor=actor,
            query_id=query_id,
            context=context,
            outcome=outcome,
        )

    def search_executed(self, *, actor: Optional[str], query_id: Optional[str], context: Any, outcome: object) -> None:
        self._log_event(
            action="SEARCH_EXECUTED",
            actor=actor,
            query_id=query_id,
            context=context,
            outcome=outcome,
        )

    def authority_evaluated(
        self, *, actor: Optional[str], query_id: Optional[str], context: Any, outcome: object
    ) -> None:
        self._log_event(
            action="AUTHORITY_EVALUATED",
            actor=actor,
            query_id=query_id,
            context=context,
            outcome=outcome,
        )

    def results_filtered(
        self, *, actor: Optional[str], query_id: Optional[str], context: Any, outcome: object
    ) -> None:
        self._log_event(
            action="RESULTS_FILTERED",
            actor=actor,
            query_id=query_id,
            context=context,
            outcome=outcome,
        )

    def response_returned(
        self, *, actor: Optional[str], query_id: Optional[str], context: Any, outcome: object
    ) -> None:
        self._log_event(
            action="RESPONSE_RETURNED",
            actor=actor,
            query_id=query_id,
            context=context,
            outcome=outcome,
        )


audit_logger = AuditLogger()
