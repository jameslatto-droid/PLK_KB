import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.authority.app.context import AuthorityContext  # type: ignore
from modules.authority.app.engine import evaluate_document_access  # type: ignore
from modules.metadata.app import models  # type: ignore
from modules.metadata.app.db import connection_cursor  # type: ignore
from modules.metadata.app.repository import (  # type: ignore
    AccessRuleRepository,
    DocumentRepository,
)


@pytest.fixture()
def cleanup_ids():
    created_ids = []
    yield created_ids
    _cleanup_documents(created_ids)


def _insert_doc(authority_level: str) -> str:
    doc_id = f"doc-{uuid.uuid4()}"
    doc = models.Document(
        document_id=doc_id,
        title="Stage 5 Doc",
        document_type="TEST",
        authority_level=authority_level,
    )
    DocumentRepository.insert(doc)
    return doc_id


def _add_rule(doc_id: str, *, project_code=None, discipline=None, classification=None, commercial=None, roles=None):
    rule = models.AccessRule(
        document_id=doc_id,
        project_code=project_code,
        discipline=discipline,
        classification=classification,
        commercial_sensitivity=commercial,
        allowed_roles=roles or [],
    )
    AccessRuleRepository.insert(rule)
    return rule.rule_id


def _cleanup_documents(doc_ids):
    if not doc_ids:
        return
    with connection_cursor() as cur:
        cur.execute("DELETE FROM audit_log WHERE document_id = ANY(%s)", (doc_ids,))
        cur.execute("DELETE FROM access_rules WHERE document_id = ANY(%s)", (doc_ids,))
        cur.execute("DELETE FROM documents WHERE document_id = ANY(%s)", (doc_ids,))


def test_stage5_unknown_authority_denied(cleanup_ids):
    doc_id = _insert_doc("NOT_A_LEVEL")
    cleanup_ids.append(doc_id)
    _add_rule(doc_id, project_code="P1", discipline="eng", roles=["viewer"])

    context = AuthorityContext(user="sam", roles=["viewer"], project_codes=["P1"], discipline="eng")
    decision = evaluate_document_access(context, doc_id, query_id=str(uuid.uuid4()))
    assert decision.allowed is False
    assert "unknown_authority" in decision.reasons


def test_stage5_missing_access_rules_denied(cleanup_ids):
    doc_id = _insert_doc("AUTHORITATIVE")
    cleanup_ids.append(doc_id)

    context = AuthorityContext(user="taylor", roles=["viewer"], project_codes=["P1"], discipline="eng")
    decision = evaluate_document_access(context, doc_id, query_id=str(uuid.uuid4()))
    assert decision.allowed is False
    assert "no_access_rules" in decision.reasons


def test_stage5_or_logic_allows_any_rule(cleanup_ids):
    doc_id = _insert_doc("REFERENCE")
    cleanup_ids.append(doc_id)
    _add_rule(doc_id, project_code="P0", discipline="eng", roles=["admin"])
    _add_rule(doc_id, project_code="P2", discipline="eng", roles=["viewer"])

    context = AuthorityContext(user="jules", roles=["viewer"], project_codes=["P2"], discipline="eng")
    decision = evaluate_document_access(context, doc_id, query_id=str(uuid.uuid4()))
    assert decision.allowed is True
    assert decision.matched_rule_ids
