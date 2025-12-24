---
type: summary
project: CISEC
project-code: P-2024-001
status: active
stage: 2
tags: [cisec, indexing, opensearch, qdrant]
---

# Indexing Module – PLK_KB

## Purpose

This module builds and maintains **derived indexes** for retrieval:
- lexical index (OpenSearch)
- vector index (Qdrant)

It:
- consumes chunks
- writes derived index state
- records index versions

It does **not**:
- store raw content as source of truth
- assign authority
- perform retrieval orchestration
- call LLMs

All behaviour must comply with `docs/06_module_contracts.md`.
