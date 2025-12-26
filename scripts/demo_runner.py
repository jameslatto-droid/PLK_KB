#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch
from qdrant_client import QdrantClient

for env_path in [ROOT / "env" / ".env", ROOT / "ops" / "docker" / ".env"]:
    if env_path.exists():
        load_dotenv(env_path)

endpoint = os.getenv("MINIO_ENDPOINT")
if endpoint and "://" not in endpoint:
    os.environ["MINIO_ENDPOINT"] = f"http://{endpoint}"

from modules.authority.app.context import AuthorityContext
from modules.chunking.app.pipeline import chunk_extracted_text
from modules.hybrid_search.app.search import hybrid_search
from modules.ingestion.app.cli import ingest_txt
from modules.metadata.app import models
from modules.metadata.app.bootstrap import ensure_schema
from modules.metadata.app.db import connection_cursor
from modules.metadata.app.repository import AccessRuleRepository
from modules.vector_indexing.app import config as vector_config
from modules.vector_indexing.app.pipeline import index_all_chunks as index_vectors
from modules.indexing.app.pipeline import index_all_chunks as index_lexical
from modules.indexing.app.opensearch_client import get_client as get_os_client


QUERY = "deployment test"


def _fail(message: str) -> None:
    print(message)
    print("FINAL VERDICT: FAIL")
    raise SystemExit(1)


def _resolve_data_path() -> Path:
    win_path = Path(r"D:\TestData")
    linux_path = Path("/mnt/d/TestData")
    if win_path.exists():
        return win_path
    if linux_path.exists():
        return linux_path
    _fail("Ingestion path missing: D:\\TestData or /mnt/d/TestData not found")
    raise SystemExit(1)


def _list_txt_files(root: Path) -> List[Path]:
    files = sorted([p for p in root.rglob("*.txt") if p.is_file()])
    if not files:
        _fail(f"No .txt files found under {root}")
    return files


def _ingest_files(files: Iterable[Path]) -> List[Tuple[str, str, str]]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    results: List[Tuple[str, str, str]] = []
    for idx, path in enumerate(files, start=1):
        doc_id = f"DEMO-{run_id}-{idx:04d}"
        version_id, artefact_id = ingest_txt(
            document_id=doc_id,
            title=path.name,
            path=path,
            document_type="DEMO",
            authority_level="AUTHORITATIVE",
        )
        results.append((doc_id, version_id, artefact_id))
    return results


def _insert_access_rules(doc_ids: Iterable[str]) -> None:
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


def _index_and_validate() -> Tuple[int, int]:
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

    if os_count <= 0 or points_count <= 0:
        _fail("Index validation failed: OpenSearch or Qdrant count is zero")
    return os_count, points_count


def _fetch_audit_examples(query_id: str) -> List[str]:
    rows: List[str] = []
    with connection_cursor(dict_cursor=True) as cur:
        cur.execute(
            """
            SELECT action, document_id, details
            FROM audit_log
            WHERE details->>'query_id' = %s
              AND action IN ('AUTHZ_ALLOW', 'AUTHZ_DENY')
            ORDER BY audit_id DESC
            LIMIT 2
            """,
            (query_id,),
        )
        for row in cur.fetchall():
            rows.append(f"{row['action']} doc={row['document_id']} details={row['details']}")
    return rows


def main() -> None:
    ensure_schema()

    data_root = _resolve_data_path()
    files = _list_txt_files(data_root)
    ingested = _ingest_files(files)
    print(f"Ingested {len(ingested)} artefacts")

    _insert_access_rules([doc_id for doc_id, _, _ in ingested])

    for _, _, artefact_id in ingested:
        chunk_extracted_text(artefact_id)

    os_count, q_count = _index_and_validate()

    ctx_super = AuthorityContext(
        user="jim",
        roles=["SUPERUSER"],
        project_codes=[],
        discipline="general",
        classification=None,
        commercial_sensitivity=None,
    )
    ctx_test = AuthorityContext(
        user="test_alice",
        roles=["TEST_USER"],
        project_codes=[],
        discipline="general",
        classification="REFERENCE",
        commercial_sensitivity=None,
    )
    ctx_restricted = AuthorityContext(
        user="test_bob",
        roles=["TEST_USER"],
        project_codes=[],
        discipline="general",
        classification="CONFIDENTIAL",
        commercial_sensitivity=None,
    )

    resp_super = hybrid_search(QUERY, context=ctx_super, top_k=5)
    resp_test = hybrid_search(QUERY, context=ctx_test, top_k=5)
    resp_restricted = hybrid_search(QUERY, context=ctx_restricted, top_k=5)

    super_count = len(resp_super["results"])
    test_count = len(resp_test["results"])
    restricted_count = len(resp_restricted["results"])

    print("\n=== DEMO RUNNER SUMMARY ===\n")
    print("Ingestion:")
    print(f"  ✔ Artefacts ingested: {len(ingested)}")
    print("\nIndexing:")
    print(f"  ✔ OpenSearch documents: {os_count}")
    print(f"  ✔ Qdrant vectors: {q_count}")
    print("\nSearch Results:")
    print(f"  ✔ Jim (SUPERUSER): {super_count} results (EXPECTED: >0)")
    print(f"  ✔ Alice (TEST_USER + REFERENCE): {test_count} results (EXPECTED: >0)")
    print(f"  ✔ Bob (TEST_USER + CONFIDENTIAL): {restricted_count} results (EXPECTED: 0)")

    auth_ok = super_count > 0 and test_count > 0 and restricted_count == 0
    if not auth_ok:
        _fail("Authorization expectations did not match")

    print("\nAuthorization:")
    print("  ✔ SUPERUSER override working")
    print("  ✔ Classification gating working")
    print("  ✔ Deny-by-default enforced")

    print("\nAudit Examples:")
    for label, resp in [
        ("Jim", resp_super),
        ("Alice", resp_test),
        ("Bob", resp_restricted),
    ]:
        examples = _fetch_audit_examples(resp["query_id"])
        if examples:
            print(f"  {label}: {examples[0]}")
        else:
            print(f"  {label}: No audit examples found for query_id={resp['query_id']}")

    print("\nFINAL VERDICT: PASS")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        _fail(f"Unhandled error: {exc!r}")
