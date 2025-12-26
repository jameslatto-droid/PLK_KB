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


def test_response_contract_and_explanations(monkeypatch):
    monkeypatch.setattr(audit_module.AuditLogRepository, "insert_event", lambda event: None)

    def fake_lex(query: str, top_k: int):
        return [
            {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "artefact_id": "art-1",
                "content": "alpha content",
                "lexical_score": 2.0,
                "normalized_lexical_score": 0.8,
            }
        ]

    def fake_sem(query: str, top_k: int):
        return [
            {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "artefact_id": "art-1",
                "semantic_score": 1.5,
                "normalized_semantic_score": 0.6,
            }
        ]

    def fake_eval(context: AuthorityContext, document_id: str, *, query_id=None):
        return AccessDecision(
            document_id=document_id, allowed=True, reasons=["rule_match"], matched_rule_ids=[42]
        )

    monkeypatch.setattr(hybrid_search, "_search_lexical", fake_lex)
    monkeypatch.setattr(hybrid_search, "_search_semantic", fake_sem)
    monkeypatch.setattr(hybrid_search, "evaluate_document_access", fake_eval)

    ctx = AuthorityContext(user="tester", roles=["viewer"], project_codes=["P1"], discipline="eng")
    response = hybrid_search.hybrid_search("alpha", context=ctx, top_k=1, query_id="test-query-id")

    assert response["query_id"] == "test-query-id"
    assert response["query"] == "alpha"
    assert response["timestamp"]
    assert len(response["results"]) == 1

    result = response["results"][0]
    assert result["document_id"] == "doc-1"
    assert result["chunk_id"] == "chunk-1"
    assert result["snippet"]
    assert result["scores"]["lexical"] == 2.0
    assert result["scores"]["semantic"] == 1.5
    assert result["authority"]["decision"] == "ALLOW"
    assert result["authority"]["matched_rule_ids"] == [42]
    assert "why_matched" in result["explanation"]
    assert "why_allowed" in result["explanation"]
    assert "why_ranked" in result["explanation"]
    assert "42" in result["explanation"]["why_allowed"]


def test_missing_explanation_fails(monkeypatch):
    monkeypatch.setattr(audit_module.AuditLogRepository, "insert_event", lambda event: None)

    def fake_lex(query: str, top_k: int):
        return [
            {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "artefact_id": "art-1",
                "content": "alpha content",
                "lexical_score": 0.0,
                "normalized_lexical_score": 0.0,
            }
        ]

    def fake_sem(query: str, top_k: int):
        return []

    def fake_eval(context: AuthorityContext, document_id: str, *, query_id=None):
        return AccessDecision(
            document_id=document_id, allowed=True, reasons=["rule_match"], matched_rule_ids=[1]
        )

    monkeypatch.setattr(hybrid_search, "_search_lexical", fake_lex)
    monkeypatch.setattr(hybrid_search, "_search_semantic", fake_sem)
    monkeypatch.setattr(hybrid_search, "evaluate_document_access", fake_eval)

    ctx = AuthorityContext(user="tester", roles=["viewer"], project_codes=["P1"], discipline="eng")
    with pytest.raises(RuntimeError):
        hybrid_search.hybrid_search("alpha", context=ctx, top_k=1, query_id="qid")


def test_missing_query_id_rejected():
    with pytest.raises(RuntimeError):
        hybrid_search._build_response(query_id="", timestamp="now", query="alpha", results=[])
