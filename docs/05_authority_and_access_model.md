---
type: authority
project: CISEC
project-code: P-2024-001
status: active
stage: 2
tags: [cisec, authority, access-control, governance]
---

# Authority & Access Model – PLK_KB

## 1. Purpose

This document defines how **authority, trust, and access** are enforced across the platform.

## 2. Authority Model

Authority is explicit and metadata-driven.

Only AUTHORITATIVE documents may override conflicting information.

## 3. Retrieval Precedence

1. AUTHORITATIVE (latest)
2. AUTHORITATIVE (older)
3. REFERENCE
4. DRAFT (explicit only)

## 4. Access Control Model

Access is enforced before retrieval using metadata dimensions:
- Project
- Discipline
- Commercial sensitivity
- Classification

## 5. LLM Guardrails

LLMs:
- only see authorised chunks
- must cite document IDs and versions
- cannot introduce new facts

## 6. Audit & Traceability

Every answer must log:
- user
- timestamp
- document IDs and versions
- model version
- index version
