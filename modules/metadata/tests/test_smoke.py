import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.metadata.app import models
from modules.metadata.app.repository import (
    DocumentRepository,
    DocumentVersionRepository,
    ArtefactRepository,
)
from modules.metadata.app.db import connection_cursor


def test_insert_and_readback_roundtrip():
    doc_id = f"doc-{uuid.uuid4()}"
    ver_id = f"ver-{uuid.uuid4()}"
    artefact_id = f"art-{uuid.uuid4()}"

    doc = models.Document(
        document_id=doc_id,
        title="Test Document",
        document_type="TEST",
        authority_level="DRAFT",
    )
    DocumentRepository.insert(doc)

    fetched_doc = DocumentRepository.get(doc_id)
    assert fetched_doc is not None
    assert fetched_doc["document_id"] == doc_id
    assert fetched_doc["status"] == "active"

    ver = models.DocumentVersion(
        version_id=ver_id,
        document_id=doc_id,
        version_label="A",
        source_path="/tmp/file.pdf",
        checksum="abc123",
    )
    DocumentVersionRepository.insert(ver)

    fetched_ver = DocumentVersionRepository.get(ver_id)
    assert fetched_ver is not None
    assert fetched_ver["document_id"] == doc_id
    assert fetched_ver["version_label"] == "A"

    artefact = models.Artefact(
        artefact_id=artefact_id,
        version_id=ver_id,
        artefact_type="RAW_FILE",
        storage_path="s3://bucket/file",
    )
    ArtefactRepository.insert(artefact)

    artefacts = ArtefactRepository.get_by_version(ver_id)
    assert any(a["artefact_id"] == artefact_id for a in artefacts)

    _cleanup_rows(artefact_id=artefact_id, ver_id=ver_id, doc_id=doc_id)


def _cleanup_rows(*, artefact_id: str, ver_id: str, doc_id: str) -> None:
    # Hard delete in dependency order to keep test idempotent.
    with connection_cursor() as cur:
        cur.execute("DELETE FROM chunks WHERE artefact_id = %s", (artefact_id,))
        cur.execute("DELETE FROM artefacts WHERE artefact_id = %s", (artefact_id,))
        cur.execute("DELETE FROM document_versions WHERE version_id = %s", (ver_id,))
        cur.execute("DELETE FROM access_rules WHERE document_id = %s", (doc_id,))
        cur.execute("DELETE FROM documents WHERE document_id = %s", (doc_id,))
