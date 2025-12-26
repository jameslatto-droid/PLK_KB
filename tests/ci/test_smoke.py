import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

psycopg2 = pytest.importorskip("psycopg2")
pytest.importorskip("opensearchpy")
pytest.importorskip("qdrant_client")
pytest.importorskip("sentence_transformers")
pytest.importorskip("minio")

from opensearchpy import OpenSearch
from qdrant_client import QdrantClient

from modules.authority.app.context import AuthorityContext  # type: ignore
from modules.hybrid_search.app.search import hybrid_search  # type: ignore
from modules.ingestion.app.cli import ingest_txt  # type: ignore
from modules.metadata.app.bootstrap import ensure_schema  # type: ignore
from modules.metadata.app import models  # type: ignore
from modules.metadata.app.config import settings as metadata_settings  # type: ignore
from modules.metadata.app.db import connection_cursor  # type: ignore
from modules.metadata.app.repository import AccessRuleRepository  # type: ignore
from modules.chunking.app.pipeline import chunk_extracted_text  # type: ignore
from modules.indexing.app.pipeline import index_all_chunks as index_lexical  # type: ignore
from modules.indexing.app.opensearch_client import get_client as get_os_client  # type: ignore
from modules.vector_indexing.app.pipeline import index_all_chunks as index_vectors  # type: ignore
from modules.vector_indexing.app import config as vector_config  # type: ignore


def _service_available() -> tuple[bool, str]:
    try:
        conn = psycopg2.connect(
            dbname=metadata_settings.db_name,
            user=metadata_settings.db_user,
            password=metadata_settings.db_password,
            host=metadata_settings.db_host,
            port=metadata_settings.db_port,
            connect_timeout=1,
        )
        conn.close()
    except Exception as exc:
        return False, f"Postgres not available: {exc!r}"

    try:
        client: OpenSearch = get_os_client()
        client.info()
    except Exception as exc:
        return False, f"OpenSearch not available: {exc!r}"

    try:
        q_client = QdrantClient(
            host=vector_config.settings.qdrant_host,
            port=vector_config.settings.qdrant_port,
            https=vector_config.settings.qdrant_https,
            api_key=vector_config.settings.qdrant_api_key,
        )
        q_client.get_collections()
    except Exception as exc:
        return False, f"Qdrant not available: {exc!r}"

    return True, ""


def _create_temp_files() -> list[Path]:
    temp_dir = Path(tempfile.mkdtemp(prefix="plk_smoke_"))
    files = []
    for idx in range(2):
        path = temp_dir / f"smoke_{idx}.txt"
        path.write_text(f"smoke test content {idx}", encoding="utf-8")
        files.append(path)
    return files


def _cleanup(doc_ids: list[str], artefact_ids: list[str]) -> None:
    if not doc_ids:
        return
    with connection_cursor() as cur:
        cur.execute("DELETE FROM audit_log WHERE document_id = ANY(%s)", (doc_ids,))
        cur.execute("DELETE FROM chunks WHERE artefact_id = ANY(%s)", (artefact_ids,))
        cur.execute("DELETE FROM access_rules WHERE document_id = ANY(%s)", (doc_ids,))
        cur.execute("DELETE FROM artefacts WHERE artefact_id = ANY(%s)", (artefact_ids,))
        cur.execute(
            "DELETE FROM document_versions WHERE document_id = ANY(%s)", (doc_ids,)
        )
        cur.execute("DELETE FROM documents WHERE document_id = ANY(%s)", (doc_ids,))


def test_ci_smoke_end_to_end():
    available, reason = _service_available()
    if not available:
        pytest.skip(reason)

    ensure_schema()

    files = _create_temp_files()
    doc_ids: list[str] = []
    artefact_ids: list[str] = []
    try:
        for path in files:
            doc_id = f"CI-SMOKE-{uuid.uuid4()}"
            version_id, artefact_id = ingest_txt(
                document_id=doc_id,
                title=path.name,
                path=path,
                document_type="SMOKE",
                authority_level="AUTHORITATIVE",
            )
            doc_ids.append(doc_id)
            artefact_ids.append(artefact_id)

        for doc_id in doc_ids:
            AccessRuleRepository.insert(
                models.AccessRule(
                    document_id=doc_id,
                    project_code=None,
                    discipline=None,
                    classification=None,
                    commercial_sensitivity=None,
                    allowed_roles=["SUPERUSER"],
                )
            )
            AccessRuleRepository.insert(
                models.AccessRule(
                    document_id=doc_id,
                    project_code=None,
                    discipline=None,
                    classification="REFERENCE",
                    commercial_sensitivity=None,
                    allowed_roles=["TEST_USER"],
                )
            )

        for artefact_id in artefact_ids:
            chunk_extracted_text(artefact_id)

        lex_count = index_lexical()
        os_client: OpenSearch = get_os_client()
        os_client.indices.refresh(index="plk_chunks_v1")
        os_count = os_client.count(index="plk_chunks_v1").get("count", 0)

        vec_count = index_vectors()
        q_client = QdrantClient(
            host=vector_config.settings.qdrant_host,
            port=vector_config.settings.qdrant_port,
            https=vector_config.settings.qdrant_https,
            api_key=vector_config.settings.qdrant_api_key,
        )
        collection = q_client.get_collection(vector_config.settings.collection_name)
        points_count = getattr(collection, "points_count", 0) or 0

        if lex_count <= 0 or os_count <= 0:
            pytest.fail("Indexing failed: OpenSearch count is zero")
        if vec_count <= 0 or points_count <= 0:
            pytest.fail("Indexing failed: Qdrant points count is zero")

        ctx_super = AuthorityContext(
            user="ci_superuser",
            roles=["SUPERUSER"],
            project_codes=[],
            discipline="general",
            classification=None,
            commercial_sensitivity=None,
        )
        ctx_test = AuthorityContext(
            user="ci_test_user",
            roles=["TEST_USER"],
            project_codes=[],
            discipline="general",
            classification="REFERENCE",
            commercial_sensitivity=None,
        )
        ctx_restricted = AuthorityContext(
            user="ci_test_user_restricted",
            roles=["TEST_USER"],
            project_codes=[],
            discipline="general",
            classification="CONFIDENTIAL",
            commercial_sensitivity=None,
        )

        resp_super = hybrid_search("deployment test", context=ctx_super, top_k=3)
        resp_test = hybrid_search("deployment test", context=ctx_test, top_k=3)
        resp_restricted = hybrid_search("deployment test", context=ctx_restricted, top_k=3)
        resp_none = hybrid_search("deployment test", context=None, top_k=3)

        if len(resp_super["results"]) < 1:
            pytest.fail("Authority check failed: SUPERUSER expected results")
        if len(resp_test["results"]) < 1:
            pytest.fail("Authority check failed: TEST_USER expected results")
        if len(resp_restricted["results"]) != 0:
            pytest.fail("Authority check failed: restricted user should have 0 results")
        if len(resp_none["results"]) != 0:
            pytest.fail("Authority check failed: no context should have 0 results")

        print("CI SMOKE TEST: PASS")
    except Exception as exc:
        print(f"CI SMOKE TEST: FAIL\nReason: {exc}")
        raise
    finally:
        _cleanup(doc_ids, artefact_ids)
