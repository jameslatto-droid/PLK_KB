---
type: requirements-index
project: CISEC
project-code: P-2024-001
status: active
stage: 2
tags: [cisec, dos, delivery-plan]
---

# Phased Build Plan & Technical DoS

## Phase 0 – Governance & Foundations
- Document ID scheme
- Authority levels
- Data classification
- Architectural rules

---

## Phase 1 – Core Platform
- Object storage
- Metadata database
- Document registration
- Basic ingestion

**Exit Criteria**
- Artefacts traceable
- No AI components

---

## Phase 2 – Search & Indexing
- Lexical search
- Vector search
- Chunking rules
- Incremental indexing

---

## Phase 3 – Drawings & Models
- Title block extraction
- Drawing previews
- CAD metadata extraction
- Confidence tagging

---

## Phase 4 – Local RAG
- Hybrid retrieval
- Reranking
- Local LLM integration
- Citation enforcement

---

## Phase 5 – Compilation & Analysis
- Dataset extraction
- Repeatable analytical jobs
- Exportable outputs

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
