import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.authority.app.context import AuthorityContext  # type: ignore
from modules.authority.app.evaluator import get_allowed_document_ids  # type: ignore
from modules.metadata.app import models  # type: ignore
from modules.metadata.app.repository import (  # type: ignore
    AccessRuleRepository,
    DocumentRepository,
)
from modules.metadata.app.db import connection_cursor  # type: ignore


@pytest.fixture()
def cleanup_ids():
    created_ids = []
    yield created_ids
    _cleanup_documents(created_ids)


def _insert_doc_with_rule(*, authority_level: str, project_code: str, discipline: str, allowed_roles):
    doc_id = f"doc-{uuid.uuid4()}"
    doc = models.Document(
        document_id=doc_id,
        title="Test Doc",
        document_type="TEST",
        authority_level=authority_level,
    )
    DocumentRepository.insert(doc)

    rule = models.AccessRule(
        document_id=doc_id,
        project_code=project_code,
        discipline=discipline,
        classification=None,
        allowed_roles=allowed_roles,
    )
    AccessRuleRepository.insert(rule)
    return doc_id


def _cleanup_documents(doc_ids):
    if not doc_ids:
        return
    with connection_cursor() as cur:
        cur.execute("DELETE FROM access_rules WHERE document_id = ANY(%s)", (doc_ids,))
        cur.execute("DELETE FROM documents WHERE document_id = ANY(%s)", (doc_ids,))


def test_allows_when_rule_matches(cleanup_ids):
    doc_id = _insert_doc_with_rule(
        authority_level="AUTHORITATIVE",
        project_code="P-1",
        discipline="eng",
        allowed_roles=["engineer"],
    )
    cleanup_ids.append(doc_id)

    context = AuthorityContext(
        user="alice",
        roles=["engineer"],
        project_codes=["P-1"],
        discipline="eng",
    )

    allowed = get_allowed_document_ids(context)
    assert doc_id in allowed


def test_role_mismatch_excludes(cleanup_ids):
    doc_id = _insert_doc_with_rule(
        authority_level="AUTHORITATIVE",
        project_code="P-1",
        discipline="eng",
        allowed_roles=["manager"],
    )
    cleanup_ids.append(doc_id)

    context = AuthorityContext(
        user="bob",
        roles=["engineer"],
        project_codes=["P-1"],
        discipline="eng",
    )

    allowed = get_allowed_document_ids(context)
    assert doc_id not in allowed


def test_project_mismatch_excludes(cleanup_ids):
    doc_id = _insert_doc_with_rule(
        authority_level="REFERENCE",
        project_code="P-2",
        discipline="eng",
        allowed_roles=["engineer"],
    )
    cleanup_ids.append(doc_id)

    context = AuthorityContext(
        user="carol",
        roles=["engineer"],
        project_codes=["P-1"],
        discipline="eng",
    )

    allowed = get_allowed_document_ids(context)
    assert doc_id not in allowed


def test_unknown_authority_denied(cleanup_ids):
    doc_id = _insert_doc_with_rule(
        authority_level="UNKNOWN",
        project_code="P-1",
        discipline="eng",
        allowed_roles=["engineer"],
    )
    cleanup_ids.append(doc_id)

    context = AuthorityContext(
        user="dave",
        roles=["engineer"],
        project_codes=["P-1"],
        discipline="eng",
    )

    allowed = get_allowed_document_ids(context)
    assert doc_id not in allowed


def test_draft_requires_explicit_rule(cleanup_ids):
    doc_id = _insert_doc_with_rule(
        authority_level="DRAFT",
        project_code="P-1",
        discipline="eng",
        allowed_roles=["engineer"],
    )
    cleanup_ids.append(doc_id)

    context = AuthorityContext(
        user="erin",
        roles=["engineer"],
        project_codes=["P-1"],
        discipline="eng",
    )

    allowed = get_allowed_document_ids(context)
    assert doc_id in allowed
