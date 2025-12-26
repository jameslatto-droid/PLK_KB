#!/usr/bin/env python
"""
Deterministic demo runner for PLK_KB.

Flow:
- Optional preflight via smoke
- Ingest demo folder (idempotent)
- Run searches under different contexts (ALLOW + DENY)
- Verify audit coverage
- Summarize next steps
"""

import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from modules.metadata.app.db import connection_cursor  # type: ignore
from modules.metadata.app.repository import ArtefactRepository  # type: ignore
from modules.ingestion.app.cli import ingest_txt  # type: ignore
from modules.chunking.app.pipeline import chunk_extracted_text  # type: ignore
from modules.indexing.app.pipeline import index_all_chunks as index_text  # type: ignore
from modules.vector_indexing.app.pipeline import index_all_chunks as index_vector  # type: ignore
from modules.hybrid_search.app.search import hybrid_search  # type: ignore
from modules.authority.app.policy import load_default_context  # type: ignore

SMOKE_PATH = ROOT / "tools" / "smoke.py"
DEFAULT_ROOT = Path(os.getenv("NEXT_PUBLIC_PLK_INGESTION_ROOT") or "/home/jim/PLK_KB/data/testdata")
WINDOWS_DEFAULT = Path("D:/TestData")


def _log(msg: str) -> None:
    print(f"[DEMO] {msg}")


def _fail(msg: str) -> None:
    _log(f"{msg} FAIL")
    sys.exit(1)


def _run_smoke() -> None:
    if not SMOKE_PATH.exists():
        _log("Smoke script missing, skipping preflight")
        return
    _log("Running smoke preflight...")
    env = os.environ.copy()
    env.setdefault("PLK_ROOT", str(ROOT))
    env.setdefault("PYTHONPATH", str(ROOT))
    proc = subprocess.run([str(ROOT / ".venv" / "bin" / "python"), str(SMOKE_PATH)], env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        _log(proc.stdout)
        _log(proc.stderr)
        _fail("Smoke preflight failed")
    _log("Smoke preflight OK")


def _resolve_ingest_root() -> Path:
    if DEFAULT_ROOT.exists():
        return DEFAULT_ROOT
    if WINDOWS_DEFAULT.exists():
        return WINDOWS_DEFAULT
    raise RuntimeError(f"Ingestion root not found. Tried {DEFAULT_ROOT} and {WINDOWS_DEFAULT}")


def _discover_files(root: Path) -> List[Path]:
    paths: List[Path] = []
    for p in root.glob("**/*.txt"):
        if p.is_file():
            paths.append(p)
    return paths


def _ingest_files(files: List[Path]) -> List[Tuple[str, str]]:
    ingested: List[Tuple[str, str]] = []
    for idx, path in enumerate(files, start=1):
        doc_id = f"DEMO-{idx:03d}"
        _, artefact_id = ingest_txt(
            document_id=doc_id,
            title=path.name,
            path=path,
            document_type="DEMO",
            authority_level="REFERENCE",
        )
        ingested.append((doc_id, artefact_id))
    return ingested


def _chunk(artefact_ids: List[str]) -> int:
    total = 0
    for artefact_id in artefact_ids:
        count, _ = chunk_extracted_text(artefact_id)
        total += count
    return total


def _reindex() -> Tuple[int, int]:
    lex = index_text()
    vec = index_vector()
    return lex, vec


def _search(query: str, actor: str, roles: List[str], classification: str) -> Tuple[int, str, dict]:
    os.environ["PLK_ACTOR"] = actor
    os.environ["PLK_CONTEXT_ROLES"] = ",".join(roles)
    os.environ["PLK_CONTEXT_CLASSIFICATION"] = classification
    ctx = load_default_context()
    result = hybrid_search(query, context=ctx, top_k=3, query_id=f"demo-{uuid.uuid4().hex}")
    results = result.get("results") or []
    count = len(results)
    decision = "ALLOW" if count > 0 else "DENY"
    return count, decision, result


def _audit_counts(query_ids: List[str]) -> int:
    with connection_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM audit_log WHERE details->>'query_id' = ANY(%s);",
            (query_ids,),
        )
        return cur.fetchone()[0]


def _artefact_count() -> int:
    return len(ArtefactRepository.list() or [])


def main() -> None:
    try:
        _run_smoke()
        ingest_root = _resolve_ingest_root()
        files = _discover_files(ingest_root)
        if not files:
            raise RuntimeError(f"No .txt files found under {ingest_root}")
        _log(f"Discovered {len(files)} file(s) in {ingest_root}")

        # Use first few files for a fast demo
        files = files[:3]
        ingested = _ingest_files(files)
        artefact_ids = [a for _, a in ingested]
        _log(f"Ingested {len(ingested)} artefact(s)")

        chunks = _chunk(artefact_ids)
        _log(f"Chunked {chunks} chunk(s)")

        lex_count, vec_count = _reindex()
        _log(f"Lexical index size: {lex_count} | Vector index size: {vec_count}")

        query_text = files[0].read_text(encoding="utf-8").splitlines()[0][:200] or "demo"
        verdicts = []
        query_ids: List[str] = []

        scenarios = [
            ("demo_superuser", ["SUPERUSER"], "REFERENCE", "EXPECT_ALLOW"),
            ("demo_user_ref", ["USER"], "REFERENCE", "EXPECT_ALLOW"),
            ("demo_contractor", ["CONTRACTOR"], "REFERENCE", "EXPECT_DENY"),
        ]

        for actor, roles, classification, expectation in scenarios:
            count, decision, result = _search(query_text, actor, roles, classification)
            query_id = result.get("query_id") or f"demo-{uuid.uuid4().hex}"
            query_ids.append(query_id)
            reason = "ALLOW (results > 0)" if decision == "ALLOW" else "DENY/empty results"
            passed = (expectation == "EXPECT_ALLOW" and count > 0) or (expectation == "EXPECT_DENY" and count == 0)
            verdicts.append((actor, roles, classification, count, decision, reason, passed))
            status = "PASS" if passed else "FAIL"
            _log(f"Search [{actor} | {','.join(roles)} | {classification}] '{query_text}' -> {count} result(s) [{decision}] {status}")

        audit_rows = _audit_counts(query_ids)
        _log(f"Audit rows for demo queries: {audit_rows}")
        artefacts_total = _artefact_count()
        _log(f"Artefacts in catalog: {artefacts_total}")

        if audit_rows < 3:
            raise RuntimeError("Audit verification failed (expected entries for each query)")
        if not all(v[-1] for v in verdicts):
            raise RuntimeError("One or more search scenarios failed expectations")

    except Exception as exc:  # noqa: BLE001
        _fail(str(exc))

    _log("Demo complete")
    _log("Next steps: visit http://localhost:3000/search and http://localhost:3000/audit, switch user context in UI header.")


if __name__ == "__main__":
    main()
