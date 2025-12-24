---
type: summary
project: CISEC
project-code: P-2024-001
status: active
stage: 2
tags: [cisec, chunking, normalisation]
---

# Chunking & Normalisation Module – PLK_KB

## Purpose

This module converts **extracted artefacts** into **stable, retrievable chunks**.

It ensures:
- structural preservation
- traceability
- deterministic behaviour

It does **not**:
- perform embeddings
- index content
- reason semantically
- call LLMs

All behaviour must comply with `docs/06_module_contracts.md`.
