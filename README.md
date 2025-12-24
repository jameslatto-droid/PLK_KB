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
