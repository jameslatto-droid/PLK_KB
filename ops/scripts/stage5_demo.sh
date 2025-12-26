#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

# Load env overrides if present
for f in "$ROOT/env/.env" "$ROOT/ops/docker/.env"; do
    if [ -f "$f" ]; then
        set -a
        # shellcheck disable=SC1090
        . "$f"
        set +a
    fi
done

# Local stack defaults (override via env if needed)
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_DB="${POSTGRES_DB:-plk_metadata}"
export POSTGRES_USER="${POSTGRES_USER:-plk_user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-change_me}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"

export MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://localhost:9000}"
export MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
export MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-change_me}"
export MINIO_BUCKET="${MINIO_BUCKET:-plk}"

export OPENSEARCH_HOST="${OPENSEARCH_HOST:-localhost}"
export OPENSEARCH_PORT="${OPENSEARCH_PORT:-9200}"
export OPENSEARCH_USERNAME="${OPENSEARCH_USERNAME:-admin}"
export OPENSEARCH_PASSWORD="${OPENSEARCH_PASSWORD:-admin}"

export QDRANT_HOST="${QDRANT_HOST:-localhost}"
export QDRANT_PORT="${QDRANT_PORT:-6333}"

# Authority defaults used by load_default_context (hybrid search) if CLI flags are omitted
export PLK_ACTOR="${PLK_ACTOR:-demo-actor}"
export PLK_CONTEXT_ROLES="${PLK_CONTEXT_ROLES:-manager}"
export PLK_CONTEXT_PROJECT_CODES="${PLK_CONTEXT_PROJECT_CODES:-ALPHA}"
export PLK_CONTEXT_DISCIPLINE="${PLK_CONTEXT_DISCIPLINE:-eng}"
export PLK_CONTEXT_CLASSIFICATION="${PLK_CONTEXT_CLASSIFICATION:-SECRET}"
export PLK_CONTEXT_COMMERCIAL_SENSITIVITY="${PLK_CONTEXT_COMMERCIAL_SENSITIVITY:-PUBLIC}"

echo "== Stage 5 demo starting =="

demo_dir="$ROOT/ops/scripts/stage5_tmp"
mkdir -p "$demo_dir"

cat >"$demo_dir/public.txt" <<'EOF'
Alpha project public overview.
This document is intended for broad sharing across roles.
Contains summary of goals and milestones.
EOF

cat >"$demo_dir/secret.txt" <<'EOF'
Alpha project strategic notes.
Restricted content for managers with SECRET clearance.
Contains upcoming launch details and vendor pricing.
EOF

echo "Files prepared under $demo_dir"

python - <<'PY'
from pathlib import Path

from modules.chunking.app.pipeline import chunk_extracted_text
from modules.ingestion.app.cli import ingest_txt
from modules.indexing.app.pipeline import index_all_chunks as index_lexical
from modules.vector_indexing.app.pipeline import index_all_chunks as index_vector
from modules.metadata.app import models
from modules.metadata.app.repository import AccessRuleRepository
from modules.metadata.app.db import connection_cursor

ROOT = Path(__file__).resolve().parents[2]
demo_dir = ROOT / "ops" / "scripts" / "stage5_tmp"

docs = [
    {
        "document_id": "demo-public",
        "title": "Alpha Overview",
        "path": demo_dir / "public.txt",
        "authority_level": "AUTHORITATIVE",
        "rule": {
            "project_code": "ALPHA",
            "discipline": "eng",
            "classification": None,
            "commercial_sensitivity": None,
            "allowed_roles": ["viewer", "manager"],
        },
    },
    {
        "document_id": "demo-secret",
        "title": "Alpha Strategy",
        "path": demo_dir / "secret.txt",
        "authority_level": "AUTHORITATIVE",
        "rule": {
            "project_code": "ALPHA",
            "discipline": "eng",
            "classification": "SECRET",
            "commercial_sensitivity": None,
            "allowed_roles": ["manager"],
        },
    },
]

doc_ids = [d["document_id"] for d in docs]
with connection_cursor() as cur:
    cur.execute("DELETE FROM access_rules WHERE document_id = ANY(%s)", (doc_ids,))
    cur.execute("DELETE FROM documents WHERE document_id = ANY(%s)", (doc_ids,))

artefact_ids = []
for doc in docs:
    version_id, artefact_id = ingest_txt(
        document_id=doc["document_id"],
        title=doc["title"],
        path=doc["path"],
        document_type="DEMO",
        authority_level=doc["authority_level"],
    )
    rule_payload = doc["rule"]
    AccessRuleRepository.insert(
        models.AccessRule(
            document_id=doc["document_id"],
            project_code=rule_payload["project_code"],
            discipline=rule_payload["discipline"],
            classification=rule_payload["classification"],
            commercial_sensitivity=rule_payload["commercial_sensitivity"],
            allowed_roles=rule_payload["allowed_roles"],
        )
    )
    chunk_count, chunk_ids = chunk_extracted_text(artefact_id)
    print(f"Ingested {doc['document_id']} -> artefact {artefact_id} | chunks: {chunk_count}")
    artefact_ids.append(artefact_id)

lex_count = index_lexical()
print(f"Lexical index rebuilt with {lex_count} chunks")
vec_count = index_vector()
print(f"Vector index rebuilt with {vec_count} chunks")
PY

python - <<'PY'
from modules.authority.app.context import AuthorityContext
from modules.hybrid_search.app.search import hybrid_search


def run(label: str, context: AuthorityContext):
    response = hybrid_search("alpha project", context=context, top_k=5)
    results = response.get("results", [])
    print(f"\n{label}: {len(results)} result(s)")
    for r in results:
        print(f" - {r['document_id']} | chunk={r['chunk_id']} | score={r['scores']['final']:.3f}")


ctx_both = AuthorityContext(
    user="alex",
    roles=["manager"],
    project_codes=["ALPHA"],
    discipline="eng",
    classification="SECRET",
    commercial_sensitivity="PUBLIC",
)

ctx_public_only = AuthorityContext(
    user="beatrice",
    roles=["viewer"],
    project_codes=["ALPHA"],
    discipline="eng",
    classification="PUBLIC",
    commercial_sensitivity="PUBLIC",
)

ctx_high_matching = AuthorityContext(
    user="charlie",
    roles=["manager"],
    project_codes=["ALPHA"],
    discipline="eng",
    classification="SECRET",
    commercial_sensitivity="PUBLIC",
)

run("Search as manager (should see both)", ctx_both)
run("Search as viewer (should see only public)", ctx_public_only)
run("Search with higher authority + project match (should see both)", ctx_high_matching)
PY

echo "\n== Stage 5 demo complete =="
