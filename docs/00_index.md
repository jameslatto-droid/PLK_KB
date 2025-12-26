---
type: index
project: CISEC
project-code: P-2024-001
status: active
stage: 5
tags: [cisec, documentation, index]
---

# Documentation Index – PLK_KB

This document is the **authoritative index** of all valid project documentation.

---

## Authoritative Documents

| ID | File | Title | Status |
|----|------|-------|--------|
| DOC-01 | 01_project_overview.md | Project Overview & Vision | Active |
| DOC-02 | 02_architecture.md | Target Architecture & Modules | Active |
| DOC-03 | 03_phased_plan_dos.md | Phased Plan & Technical DoS | Active |
| DOC-04 | 04_metadata_schema.md | Metadata Schema | Active |
| DOC-05 | 05_authority_and_access_model.md | Authority & Access Model | Active |
| DOC-06 | 06_module_contracts.md | Module Contracts | Active |
| DOC-07 | 07_database_schema.md | Database Schema | Active |
| DOC-08 | modules/api/README.md | API Module Skeleton | Active |
| DOC-09 | modules/ingestion/README.md | Ingestion Module Skeleton | Active |
| DOC-10 | modules/chunking/README.md | Chunking & Normalisation Skeleton | Active |
| DOC-11 | modules/indexing/README.md | Indexing Module Skeleton | Active |
| DOC-12 | 99_ai_usage_rules.md | AI Usage Rules | Active |
| DOC-13 | 09_stage_3_planning_and_implementation.md | Stage 3 Planning & Implementation | Active |
| DOC-14 | 11_stage_8_extraction_and_filetypes.md | Stage 8: Extraction & Filetype Expansion | Active |

---

## Governance Rules

- Only documents listed here are authoritative
- Changes to architecture or scope **must** update this index
- Superseded documents are retained, not deleted
- Stage changes require index update

---

## Stage Context

Current Stage: **5 – Authority + Audit + UI** (hybrid search, authority, audit wiring, and UI are live).

### Stage 6 – Production Hardening (next)
- Identity & auth: replace dev presets with real identity provider; session-bound context
- Authorization policy evolution: clarify classification semantics (currently equality-based), introduce policy versioning/migrations
- Audit & compliance: export/retention strategy, integrity controls, operational dashboards
- Observability & operations: health endpoints, logs/metrics, alerting, CI/CD hooks
- Deployment hardening: backups/restore, upgrades, config management
- Ingestion expansion (optional): OCR / non-text formats
- Status: not started; Stage 5 remains current operational baseline
