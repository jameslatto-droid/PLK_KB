---
type: summary
project: CISEC
project-code: P-2024-001
status: active
stage: 2
tags: [cisec, ingestion, pipelines]
---

# Ingestion Module – PLK_KB

## Purpose

The ingestion module converts **registered source files** into **derived artefacts**.

It:
- reads metadata
- processes files deterministically
- produces explicit artefacts
- records lineage

It does **not**:
- assign authority
- chunk content
- index data
- call LLMs

All behaviour must comply with `docs/06_module_contracts.md`.
