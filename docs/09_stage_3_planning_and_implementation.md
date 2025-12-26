# Stage 3: Indexing — Planning & Implementation (Retrospective)

**Phase**: 3 (Indexing)  
**Status**: COMPLETE (delivered with hybrid search + UI)  
**Date Range**: 2024-11 → 2024-12-26

## Objectives (Delivered)
1. Lexical indexing in OpenSearch (chunk-level with metadata)
2. Vector indexing in Qdrant (sentence-transformers/all-MiniLM-L6-v2)
3. Hybrid search via RRF with authority pre-filtering
4. UI surface for pipeline visibility (dashboard, search, ingest, artefacts, access rules, audit)
5. Audit + authority instrumentation for every query path (fail-closed)

## Implementation Highlights

- **OpenSearch**: BM25 on `content`, metadata filters for authority pre-filter, bulk upserts from ingestion pipeline.
- **Qdrant**: 384-dim vectors, payload carries authority metadata, cosine similarity retrieval.
- **Hybrid Search**: RRF with `k=60`, applies after each path is authority-filtered to avoid leaking denied content.
- **Authority**: OR semantics across access rules; classification match is equality-based (no clearance hierarchy). Missing
  rules => deny with reasons.
- **Audit**: `audit_log` table captures actor, action, details JSON, timestamps. Inserts are mandatory; failures abort the
  query path.
- **UI**: Next.js app router with panels for ingestion, search, artefacts, access rules, and audit. Dev-only context
  presets propagate `PLK_ACTOR`, `PLK_CONTEXT_ROLES`, `PLK_CONTEXT_CLASSIFICATION`.

## Deferred / Stage 6 Candidates
- Hierarchical classification mapping (e.g., SECRET ≥ CONFIDENTIAL) — **not implemented**; current engine uses equality
  checks.
- OCR / CAD extraction; confidence tagging for REFERENCE content.
- External auth (SSO/LDAP) and multi-tenancy boundaries.

## Lessons Learned
- **Authority timing**: Filter per index before fusion; otherwise denied content can influence rank.
- **Fail-closed audit**: Treat audit insert failures as hard failures; pipeline should stop rather than proceed silently.
- **Storage split**: Keep Postgres on ext4 (WSL restriction); place OpenSearch/Qdrant/MinIO on expandable mount.

## Verification
- Self-test exercises ingest → chunk → index → hybrid search with audit on.
- Authority tests confirm deny-by-default and equality-based classification matching.
- Audit UI exposes the append-only log with filters; no delete/edit paths exist.
