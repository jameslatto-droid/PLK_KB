# Phase 3 Status – Indexing & Retrieval

**Status**: COMPLETE (Delivered and exceeded scope)

## Delivered
- OpenSearch lexical index (BM25) with chunk-level metadata
- Qdrant vector index (sentence-transformers/all-MiniLM-L6-v2)
- Hybrid search via Reciprocal Rank Fusion (authority pre-filtered)
- Deterministic ingestion + chunking paths
- UI coverage: dashboard, self-test, search, ingestion, artefacts, access rules, audit
- Audit logging wired across pipeline (fail-closed: query fails if audit insert fails)

## Residual Risks / Follow-ups
- Classification matching is **equality-based** in authority (`rule.classification == context.classification`). Any
  hierarchical clearance model (e.g., SECRET >= CONFIDENTIAL) would require a Stage 6 backend change; presets and docs
  are adjusted to highlight equality semantics.
- Ingestion root was hardcoded; now configurable via `NEXT_PUBLIC_PLK_INGESTION_ROOT` (UI only).
- OCR / CAD extraction and confidence tagging remain explicitly deferred.

## Notes
- Access rules retain OR semantics; deny-by-default with machine-readable reasons.
- Audit log is append-only (`audit_log` table); no delete/edit paths.
- Authority filtering occurs before fusion to prevent leaking unauthorized results into ranking.

## Next
- Stage 6 (Production Hardening): consider hierarchical classification mapping, external auth, multi-tenancy, and
  deferred extraction features.
