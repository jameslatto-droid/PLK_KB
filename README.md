---
type: summary
project: CISEC
project-code: P-2024-001
status: active
stage: 2
tags: [cisec, knowledge-platform, on-prem, ai]
---

# PLK_KB – Project Local Knowledge Base

## Purpose

PLK_KB is a **local-first engineering knowledge platform** designed to manage, search, and analyse large volumes of technical information using modern retrieval and language models.

The system is intentionally designed as **infrastructure**, not an experimental chatbot.

---

## Objectives

- Manage ~1TB of technical and commercial data
- Support exact, semantic, and contextual search
- Work with documents, spreadsheets, drawings, and 3D models
- Enable local LLM-assisted reasoning (RAG)
- Preserve authority, provenance, and auditability
- Allow controlled model upgrades over time

---

## Key Principles

- Raw source data is immutable
- All derived artefacts are explicit and traceable
- Indexes are rebuildable
- Authority is metadata-driven
- LLMs consume curated context only
- Fully on-prem by default

---

## Repository Structure

```
docs/          Authoritative documentation
modules/       Logical system modules
architecture/  Logical and physical diagrams
ops/           Deployment and operational assets
```

---

## Status

- Stage: Architecture & foundations (Stage 2)
- Deployment model: Single on-site workstation
- Users: Small internal engineering team

Refer to `docs/00_index.md` for the authoritative documentation list.

---

## CI Service Dependency Notes

The PLK_KB repository includes both pure logic tests and integration-level tests.

### Required External Services (Integration Tests)

The following services must be running for full integration test coverage:

**Postgres**
- Host: localhost
- Port: 5432
- Database: plk_metadata
- User: plk_user

**OpenSearch**
- Host: localhost
- Port: 9200
- Auth: admin/admin (dev default)
- HTTPS: enabled with cert checks disabled in dev

**Qdrant**
- REST Port: 6333
- gRPC Port: 6334

**ML Embeddings**
- Python package: sentence-transformers
- Required for semantic and hybrid search paths

### If any of these services are unavailable:

- Integration tests may be skipped (not failed)
- Unit and authority logic tests must still pass

### CI Expectations

CI environments without services are expected to:
- Pass unit tests
- Skip service-bound tests with explicit reasons

CI environments with services enabled should run full test suites

This distinction is intentional and enforced to prevent false negatives while preserving fail-closed production behavior.
