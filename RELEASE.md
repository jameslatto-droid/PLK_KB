# Release Readiness Verdict

READY — Deployment is manual and service-bound, with explicit configuration and fail-closed authority/audit behavior documented.

# Scope of This Release

- Provides local-first ingestion, metadata governance, indexing, and hybrid retrieval with authority enforcement and auditability.
- Does not automate infrastructure provisioning, orchestration, or managed cloud deployment.
- Assumes operators run services via Docker / docker-compose and provide environment configuration.

# Required Services

- Postgres (metadata DB, port 5432, version 15.x as per docker-compose)
- MinIO (ingestion artifacts, ports 9000/9001, version latest)
- OpenSearch (lexical index, port 9200, version 2.x; docker-compose pins 2.11.0)
- Qdrant (vector index, ports 6333/6334, version latest)

# Required Runtime Dependencies

- sentence-transformers
- psycopg2-binary
- opensearch-py
- qdrant-client
- minio
- pydantic
- pydantic-settings
- python-dotenv

# Environment Configuration

- Use `ops/docker/env.example` as the canonical deployment env template.
- Module READMEs list defaults and required variables (see `modules/metadata/README.md`, `modules/hybrid_search/README.md`, `modules/ingestion/README.md`).
- Required env var prefixes:
  - POSTGRES_
  - MINIO_
  - OPENSEARCH_
  - QDRANT_
  - PLK_CONTEXT_*
- `.env` loading locations:
  - `env/.env` (application modules)
  - `ops/docker/.env` (docker-compose)
- Note: ensure POSTGRES_DB matches the metadata module configuration (`plk_metadata` default in code and docker-compose); set POSTGRES_DB explicitly to keep them aligned.
  - WSL constraint: Postgres data must NOT live on Windows-mounted filesystems (e.g., `/mnt/c`, `/mnt/e`). Use a Docker volume or ext4-backed path.
  - Storage placement: MinIO, OpenSearch, and (with caution) Qdrant data may reside on Windows-backed mounts like `/mnt/e/Data_Index` to absorb growth, but Postgres must remain on ext4.

# Preflight Checks (Required Before Deploy)

- Service status:
  - `docker-compose -f ops/docker/docker-compose.yml ps`
- Postgres schema accessibility:
  - `docker exec -i plk-postgres psql -U plk_user -d plk_metadata -c "\dt"`
- OpenSearch health:
  - `curl -s https://localhost:9200 -u admin:admin --insecure | grep -q cluster_name`
- Qdrant health:
  - `curl -f http://localhost:6333/health`
- MinIO health:
  - `curl -f http://localhost:9000/minio/health/live`

# Safe Deployment Order

1. Start services: `docker-compose -f ops/docker/docker-compose.yml up -d`
2. Bootstrap artefacts table: `python -m modules.metadata.app.bootstrap`
3. Apply schema: `docker exec -i plk-postgres psql -U plk_user -d plk_kb < ops/sql/01_metadata_schema.sql`
4. Ingest and index (example): `python -m modules.ingestion.app.cli ingest-txt --document-id DEMO-001 --title "Demo" --path ops/scripts/stage5_tmp/public.txt --document-type DEMO --authority-level AUTHORITATIVE`
5. Chunk and index:
   - `python -m modules.indexing.app.pipeline`
   - `python -m modules.vector_indexing.app.pipeline`
6. Hybrid search smoke test: `python -m modules.hybrid_search.app.cli "alpha project" --size 3`

# Rollback Strategy

- Rollback is manual by redeploying a previous git tag.
- No automatic DB schema rollback is provided.
- Audit logs are append-only and must persist across rollbacks.
- Docker volumes must not be deleted during rollback.

# CI and Test Expectations

- Service-bound tests are explicitly skipped when dependencies are unavailable.
- This behavior is intentional to prevent false CI failures.
- CI environments with services enabled should run full test suites.

# Demo Runner

- Run: `python scripts/demo_runner.py`
- PASS means ingestion, indexing, and authorization checks completed with expected result counts for superuser/test users and deny-by-default for restricted users.

# CI Smoke Test

- Run: `pytest tests/ci/test_smoke.py`
- Guarantees: metadata bootstrap, artefact registration, chunking, indexing, search, and authority checks succeed when required services are available.
- Skips with explicit reasons when Postgres, OpenSearch, or Qdrant are unavailable.
