#!/usr/bin/env python
"""
Lightweight end-to-end smoke test for PLK_KB.

Contract:
- Uses real services (Postgres, MinIO, OpenSearch, Qdrant); no mocks.
- Performs minimal ingest + chunk + lexical search + audit verification.
- Avoids full-corpus reindex (keeps runtime bounded, suitable for CI).
- Creates a temporary OpenSearch index and cleans up test artifacts.
"""

import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

load_dotenv(ROOT / "env" / ".env", override=False)
load_dotenv(ROOT / "ops" / "docker" / ".env", override=False)

from modules.metadata.app.db import connection_cursor  # type: ignore

TEMP_FILE = ROOT / "tmp_smoke_test.txt"


def _log(msg: str) -> None:
    print(f"[SMOKE] {msg}")


def _fail(msg: str) -> None:
    _log(f"{msg} FAIL")
    sys.exit(1)


def _check_postgres() -> None:
    _log("Checking Postgres connectivity...")
    with connection_cursor() as cur:
        cur.execute("SELECT 1;")


def _check_schema() -> None:
    _log("Checking schema tables...")
    with connection_cursor() as cur:
        cur.execute("SELECT to_regclass('public.documents');")
        row = cur.fetchone()
        if not row or row[0] is None:
            raise RuntimeError("documents table missing")


def _check_opensearch() -> None:
    _log("Checking OpenSearch...")
    from modules.indexing.app.opensearch_client import get_client as get_os_client  # type: ignore

    client = get_os_client()
    if not client.ping():
        raise RuntimeError("OpenSearch ping failed")


def _check_qdrant() -> None:
    _log("Checking Qdrant...")
    from modules.vector_indexing.app.qdrant_client import get_client as get_qdr_client  # type: ignore

    client = get_qdr_client()
    client.get_collections()  # will raise on connectivity issues


def _ingest_file(doc_id: str, content: str) -> tuple[str, str]:
    _log("Ingesting test file...")
    from modules.ingestion.app.cli import ingest_txt  # type: ignore

    TEMP_FILE.write_text(content, encoding="utf-8")
    version_id, artefact_id = ingest_txt(
        document_id=doc_id,
        title="SMOKE_TEST",
        path=TEMP_FILE,
        document_type="SMOKE_DOC",
        authority_level="REFERENCE",
    )
    return version_id, artefact_id


def _chunk(artefact_id: str) -> tuple[int, list[str]]:
    _log("Chunking artefact...")
    from modules.chunking.app.pipeline import chunk_extracted_text  # type: ignore

    count, ids = chunk_extracted_text(artefact_id)
    if count <= 0:
        raise RuntimeError("No chunks created")
    return count, ids


def _cleanup(
    *,
    document_id: str,
    version_id: str,
    artefact_id: str,
    chunk_ids: list[str],
    query_id: str,
    index_name: str,
) -> None:
    # Best-effort cleanup for CI/local: remove temporary index and test artifacts.
    try:
        from modules.indexing.app.opensearch_client import get_client as get_os_client  # type: ignore

        client = get_os_client()
        if client.indices.exists(index=index_name):
            client.indices.delete(index=index_name)
    except Exception:
        pass

    try:
        from minio import Minio
        from urllib.parse import urlparse

        endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        parsed = urlparse(endpoint)
        host = parsed.netloc or parsed.path
        secure = parsed.scheme == "https"
        bucket = os.getenv("MINIO_BUCKET", "plk-artifacts")
        client = Minio(
            host,
            access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "change_me"),
            secure=secure,
        )
        raw_key = f"raw/{document_id}/{version_id}/{TEMP_FILE.name}"
        artefact_key = f"artefacts/{document_id}/{version_id}/extracted_text.txt"
        for key in (raw_key, artefact_key):
            try:
                client.remove_object(bucket, key)
            except Exception:
                pass
    except Exception:
        pass

    try:
        with connection_cursor() as cur:
            cur.execute("DELETE FROM audit_log WHERE details->>'query_id' = %s OR document_id = %s", (query_id, document_id))
            cur.execute("DELETE FROM access_rules WHERE document_id = %s", (document_id,))
            if chunk_ids:
                cur.execute("DELETE FROM chunks WHERE chunk_id = ANY(%s)", (chunk_ids,))
            cur.execute("DELETE FROM artefacts WHERE artefact_id = %s", (artefact_id,))
            cur.execute("DELETE FROM document_versions WHERE version_id = %s", (version_id,))
            cur.execute("DELETE FROM documents WHERE document_id = %s", (document_id,))
    except Exception:
        pass


def _ensure_access_rule(document_id: str) -> None:
    _log("Seeding access rule for smoke document...")
    from modules.metadata.app import models  # type: ignore
    from modules.metadata.app.repository import AccessRuleRepository  # type: ignore

    rule = models.AccessRule(
        document_id=document_id,
        allowed_roles=["SUPERUSER"],
        classification="REFERENCE",
    )
    AccessRuleRepository.insert(rule)


def _create_temp_index(index_name: str) -> None:
    from modules.indexing.app.opensearch_client import CHUNK_INDEX_BODY, get_client  # type: ignore

    client = get_client()
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
    client.indices.create(index=index_name, body=CHUNK_INDEX_BODY)


def _index_smoke_chunks(index_name: str, artefact_id: str, document_id: str) -> None:
    _log(f"Indexing smoke chunks into OpenSearch index {index_name}...")
    from opensearchpy import helpers  # type: ignore
    from modules.indexing.app.opensearch_client import get_client  # type: ignore

    with connection_cursor(dict_cursor=True) as cur:
        cur.execute(
            """
            SELECT chunk_id, artefact_id, content, metadata
            FROM chunks
            WHERE artefact_id = %s
            ORDER BY chunk_id
            """,
            (artefact_id,),
        )
        rows = [dict(r) for r in cur.fetchall()]

    if not rows:
        raise RuntimeError("No chunks found to index")

    docs = []
    for row in rows:
        meta = row.get("metadata") or {}
        docs.append(
            {
                "chunk_id": row["chunk_id"],
                "artefact_id": row["artefact_id"],
                "document_id": document_id,
                "content": row["content"],
                "chunk_index": meta.get("chunk_index"),
                "char_start": meta.get("char_start"),
                "char_end": meta.get("char_end"),
            }
        )

    client = get_client()
    actions = [
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": doc["chunk_id"],
            "_source": doc,
        }
        for doc in docs
    ]
    helpers.bulk(client, actions)
    client.indices.refresh(index=index_name)


def _search_and_audit(index_name: str, query: str, document_id: str, query_id: str) -> None:
    _log("Running lexical search (smoke index) with audit...")
    from modules.authority.app.engine import evaluate_document_access  # type: ignore
    from modules.authority.app.policy import load_default_context  # type: ignore
    from modules.metadata.app.audit import audit_logger  # type: ignore
    from modules.indexing.app.opensearch_client import get_client  # type: ignore

    ctx = load_default_context()
    audit_logger.search_query(actor=ctx.user, query=query, context=ctx, query_id=query_id)
    decision = evaluate_document_access(ctx, document_id, query_id=query_id)
    if not decision.allowed:
        raise RuntimeError(f"Authority denied smoke document: {decision.reasons}")

    client = get_client()
    body = {
        "query": {
            "bool": {
                "must": {"match": {"content": query}},
                "filter": [{"term": {"document_id": document_id}}],
            }
        }
    }
    resp = client.search(index=index_name, body=body, size=3)
    hits = resp.get("hits", {}).get("hits", [])
    audit_logger.search_results_returned(
        actor=ctx.user,
        count=len(hits),
        document_ids=[document_id] if hits else [],
        context=ctx,
        query_id=query_id,
    )
    if not hits:
        raise RuntimeError("Search returned no results")


def _check_audit(query_id: str) -> None:
    _log("Verifying audit log...")
    with connection_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM audit_log WHERE details->>'query_id' = %s;",
            (query_id,),
        )
        count = cur.fetchone()[0]
        if count < 1:
            raise RuntimeError("No audit rows found for query_id")


def main() -> None:
    os.environ["PLK_ACTOR"] = "smoke_test"
    os.environ["PLK_CONTEXT_ROLES"] = "SUPERUSER"
    os.environ["PLK_CONTEXT_CLASSIFICATION"] = "REFERENCE"

    doc_id = f"SMOKE-{uuid.uuid4().hex}"
    query_text = f"smoke test content {uuid.uuid4().hex}"
    query_id = f"smoke-{uuid.uuid4().hex}"
    smoke_index = f"plk_smoke_{uuid.uuid4().hex}"
    os.environ["OPENSEARCH_INDEX"] = smoke_index

    version_id = ""
    artefact_id = ""
    chunk_ids: list[str] = []

    try:
        _check_postgres()
        _check_schema()
        _check_opensearch()
        _check_qdrant()
        version_id, artefact_id = _ingest_file(doc_id, query_text)
        _, chunk_ids = _chunk(artefact_id)
        _ensure_access_rule(doc_id)
        _create_temp_index(smoke_index)
        _index_smoke_chunks(smoke_index, artefact_id, doc_id)
        _search_and_audit(smoke_index, query_text, doc_id, query_id)
        _check_audit(query_id)
    except Exception as exc:  # noqa: BLE001
        _fail(f"{exc}")
    finally:
        if TEMP_FILE.exists():
            try:
                TEMP_FILE.unlink()
            except Exception:
                pass
        _cleanup(
            document_id=doc_id,
            version_id=version_id,
            artefact_id=artefact_id,
            chunk_ids=chunk_ids,
            query_id=query_id,
            index_name=smoke_index,
        )

    _log("PASS")


if __name__ == "__main__":
    main()
