---
type: requirements-index
project: CISEC
project-code: P-2024-001
status: active
stage: 2
tags: [cisec, database, schema, postgres]
---

# Database Schema – Metadata & Governance

## 1. Purpose

This document defines the **authoritative PostgreSQL schema** for metadata, governance, authority, and lineage within PLK_KB.

This database is the **control plane** of the platform.

All modules must:
- read from this schema
- write to this schema explicitly
- treat it as the source of truth

---

## 2. Design Rules

1. No binary data stored in the database
2. No derived content stored without lineage
3. No implicit authority
4. No soft deletes (status fields only)
5. IDs are stable and externally referenceable
6. No indexes, triggers, or performance optimisations at Stage 2

---

## 3. Core Tables

---

## 3.1 documents

Logical document identity.

```sql
CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    document_type TEXT NOT NULL,
    authority_level TEXT NOT NULL,
    owner TEXT,
    project_code TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
