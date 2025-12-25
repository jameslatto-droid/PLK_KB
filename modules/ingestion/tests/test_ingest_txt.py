import os
import sys
import tempfile
from pathlib import Path

import pytest
from minio import Minio

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ingestion.app.cli import ingest_txt  # type: ignore
from modules.ingestion.app.config import settings  # type: ignore
from modules.metadata.app.repository import (  # type: ignore
    DocumentRepository,
    DocumentVersionRepository,
    ArtefactRepository,
)
from modules.metadata.app.db import connection_cursor  # type: ignore


pytestmark = pytest.mark.skipif(
    os.getenv("INGEST_E2E") != "1",
    reason="Set INGEST_E2E=1 to run ingestion E2E against local stack",
)


def _minio_client():
    endpoint = settings.minio_endpoint.replace("http://", "").replace("https://", "")
    secure = settings.minio_endpoint.startswith("https")
    return Minio(
        endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=secure,
    )


def test_ingest_txt_roundtrip():
    doc_id = "doc-test-ingest"
    title = "Test TXT"
    document_type = "TEST"
    authority_level = "DRAFT"

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write("hello world")
        tmp_path = Path(tmp.name)

    version_id, artefact_id = ingest_txt(
        document_id=doc_id,
        title=title,
        path=tmp_path,
        document_type=document_type,
        authority_level=authority_level,
    )

    doc = DocumentRepository.get(doc_id)
    assert doc is not None

    ver = DocumentVersionRepository.get(version_id)
    assert ver is not None
    assert ver["document_id"] == doc_id

    artefacts = ArtefactRepository.get_by_version(version_id)
    assert any(a["artefact_id"] == artefact_id for a in artefacts)

    _cleanup(doc_id)
    tmp_path.unlink(missing_ok=True)


def _cleanup(doc_id: str) -> None:
    client = _minio_client()
    # Remove any objects under raw/ and artefacts/ for doc_id
    for prefix in [f"raw/{doc_id}", f"artefacts/{doc_id}"]:
        objects = client.list_objects(settings.minio_bucket, prefix=prefix, recursive=True)
        for obj in objects:
            client.remove_object(settings.minio_bucket, obj.object_name)

    with connection_cursor() as cur:
        cur.execute("DELETE FROM artefacts WHERE version_id IN (SELECT version_id FROM document_versions WHERE document_id = %s)", (doc_id,))
        cur.execute("DELETE FROM document_versions WHERE document_id = %s", (doc_id,))
        cur.execute("DELETE FROM access_rules WHERE document_id = %s", (doc_id,))
        cur.execute("DELETE FROM documents WHERE document_id = %s", (doc_id,))
