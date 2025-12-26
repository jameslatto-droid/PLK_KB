---
type: requirements-index
project: CISEC
project-code: P-2024-001
status: active
stage: 5
tags: [cisec, dos, delivery-plan]
---

# Phased Build Plan & Technical DoS

## Phase 0 – Governance & Foundations ✅ COMPLETE
- Document ID scheme
- Authority levels
- Data classification
- Architectural rules

---

## Phase 1 – Core Platform ✅ COMPLETE
- Object storage
- Metadata database
- Document registration
- Basic ingestion

**Exit Criteria**
- Artefacts traceable
- No AI components

---

## Phase 2 – Search & Indexing ✅ COMPLETE
- Lexical search (OpenSearch)
- Vector search (Qdrant + sentence-transformers/all-MiniLM-L6-v2)
- Chunking rules
- Incremental indexing

---

## Phase 3 – Indexing & Retrieval ✅ COMPLETE
- Hybrid search (RRF) with authority pre-filter
- UI for pipeline visibility
- Audit logging across query lifecycle (fail-closed)
- Authority deny-by-default with OR semantics; classification match is equality-based

---

## Phase 4 – Local RAG ✅ COMPLETE
- Hybrid retrieval exposed via UI
- Authority explanations surfaced
- Citation + context panels

## Phase 5 – Compilation & Analysis ✅ COMPLETE (pipeline + UI wiring)
- Dataset extraction paths stubbed behind existing pipeline
- Audit + authority applied to responses

---

## Phase 6 – Production Hardening (NEXT)
- Identity & authentication: replace dev presets with real identity provider (SSO/LDAP); session-bound context propagation
- Authorization policy evolution: clarify classification semantics (current behavior is equality-match), introduce policy versioning/migrations
- Audit & compliance: export/retention strategy, integrity controls, operational dashboards for audit visibility
- Observability & operations: health endpoints, log/metric collection, alerting, CI/CD hooks
- Deployment hardening: backups/restore, upgrade path, config management, disaster recovery drills
- Ingestion expansion (optional): OCR and non-text formats (CAD/drawings/images) as workload-driven add-ons
- Status: not started; Stage 5 remains the current operational baseline

---

## Technical DoS Requirements

### Data
- Immutable sources
- Explicit derivation
- Lineage preserved
- Authority & confidence tagging
- Versioned indexes and models

### Operations
- Idempotent pipelines
- Restartable jobs
- Manual and scheduled execution
- Observable failures

### Security
- Local-only by default
- Permission-first retrieval
- Controlled data egress
- Auditable access and answers
