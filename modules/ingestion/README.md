---
type: summary
project: CISEC
project-code: P-2024-001
status: active
stage: 5
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

## Supported formats (current)

- Text-like files: `.txt`, `.md`, `.csv`, `.log`, `.json`, `.rtf`

These are ingested as plain text via `ingest_txt`. Binary formats are intentionally excluded.

## Deferred formats (Stage 6)

- PDF, DOC, DOCX
- OCR/image ingestion (PNG/JPG, scanned PDFs)
- CAD/drawings and other binary formats
- Rich document extraction beyond plain-text handling

The UI and ingestion runner enforce an allowlist (`ALLOWED_INGEST_EXTENSIONS` in `apps/ui/lib/server/ingestRunner.ts`) to match this scope. Additional formats require Stage 6 work (extraction + authority/audit alignment).
