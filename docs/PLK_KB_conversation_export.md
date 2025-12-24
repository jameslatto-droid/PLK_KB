
# PLK_KB Project – Conversation Export

This document is an exported record of the planning and architecture discussion for the **PLK_KB (Project Local Knowledge Base)** initiative.

---

## Context

- Project: CISEC / PLK_KB
- Goal: Build a local-first, modular knowledge platform for ~1TB of engineering and commercial data
- Approach: Strong governance, contracts-first architecture, staged delivery
- Tooling: VS Code + Codex for implementation, ChatGPT for architecture and review

---

## Key Outcomes from This Conversation

### Stage 2 (Completed)
- Project overview and scope defined
- Target architecture locked
- Metadata schema established
- Authority & access model defined
- Module contracts formalised
- Database schema defined
- API, ingestion, chunking, indexing module skeletons created
- Docker-compose infrastructure baseline defined
- AI usage governance rules agreed

### Stage 3 (Planned)
- Clear implementation order established
- Explicit handover to Codex for implementation
- Deterministic-first approach mandated
- LLMs deferred until retrieval layer is stable
- Strong contract enforcement during coding

---

## Core Principles Captured

- Contracts before code
- Deterministic pipelines before AI
- Metadata and authority are the control plane
- LLMs are consumers, not decision-makers
- Everything must be rebuildable and auditable

---

## Index Alignment

The discussion resolved:
- Only documents that physically exist should appear in `docs/00_index.md`
- Module READMEs become authoritative only once created
- Stage 3 planning document added cleanly to the index

---

## Tooling Guidance

- **ChatGPT**: architecture, contracts, review, boundary enforcement
- **Codex (VS Code)**: migrations, repositories, deterministic pipelines, tests
- Rule of thumb:
  - “Should” → ChatGPT
  - “Write” → Codex

---

## Next Implementation Steps

1. PostgreSQL migrations from database schema
2. Metadata access layer
3. Minimal ingestion for one file type
4. Chunking implementation
5. Lexical search
6. Vector search & embeddings
7. Retrieval orchestration
8. Local LLM integration

---

## Notes

This export is intended as:
- a project record
- onboarding context
- architectural reference
- justification for design decisions

It is not a substitute for the authoritative documents in `docs/`.

---

_End of export_
