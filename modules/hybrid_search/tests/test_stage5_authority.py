import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.authority.app.context import AuthorityContext  # type: ignore
from modules.authority.app.engine import AccessDecision  # type: ignore
from modules.hybrid_search.app import search as hybrid_search  # type: ignore
from modules.metadata.app import audit as audit_module  # type: ignore


def test_hybrid_search_filters_denied_high_score(monkeypatch):
    monkeypatch.setattr(audit_module.AuditLogRepository, "insert_event", lambda event: None)

    def fake_lex(query: str, top_k: int):
        return [
            {
                "chunk_id": "chunk-denied",
                "document_id": "doc-denied",
                "artefact_id": "art-denied",
                "content": "denied content",
                "lexical_score": 10.0,
                "normalized_lexical_score": 1.0,
            },
            {
                "chunk_id": "chunk-allowed",
                "document_id": "doc-allowed",
                "artefact_id": "art-allowed",
                "content": "allowed content",
                "lexical_score": 1.0,
                "normalized_lexical_score": 0.1,
            },
        ]

    def fake_sem(query: str, top_k: int):
        return []

    def fake_eval(context: AuthorityContext, document_id: str, *, query_id=None):
        if document_id == "doc-denied":
            return AccessDecision(document_id=document_id, allowed=False, reasons=["no_access_rules"])
        return AccessDecision(document_id=document_id, allowed=True, matched_rule_ids=[1])

    monkeypatch.setattr(hybrid_search, "_search_lexical", fake_lex)
    monkeypatch.setattr(hybrid_search, "_search_semantic", fake_sem)
    monkeypatch.setattr(hybrid_search, "evaluate_document_access", fake_eval)

    ctx = AuthorityContext(user="tester", roles=["viewer"], project_codes=["P1"], discipline="eng")
    response = hybrid_search.hybrid_search("query", context=ctx, top_k=2)
    results = response["results"]

    assert len(results) == 1
    assert results[0]["document_id"] == "doc-allowed"


def test_audit_failure_aborts_hybrid_search(monkeypatch):
    def raise_insert(_event):
        raise RuntimeError("db down")

    monkeypatch.setattr(audit_module.AuditLogRepository, "insert_event", raise_insert)

    with pytest.raises(audit_module.AuditLogError):
        hybrid_search.hybrid_search("query", context=AuthorityContext(user="tester"), top_k=1)
