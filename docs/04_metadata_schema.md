---
type: requirements-index
project: CISEC
project-code: P-2024-001
status: active
stage: 2
tags: [cisec, metadata, schema, governance]
---

# Metadata Schema – PLK_KB

## 1. Purpose

This document defines the **canonical metadata schema** used across the PLK_KB platform.

Metadata is the **single source of truth** for:
- document identity
- authority
- versioning
- lineage
- access control
- auditability

No module may invent or bypass metadata.

## 2. Core Design Rules

1. Every file is registered before processing
2. Document IDs are stable for life
3. Versions are explicit
4. Authority is metadata-driven
5. Derived artefacts never overwrite sources
6. Metadata is queryable independently of content

## 3. Core Entities

### 3.1 Document

| Field | Type | Description |
|-----|----|----|
| document_id | string | Stable unique identifier |
| title | string | Human-readable name |
| document_type | enum | See §4.1 |
| authority_level | enum | See §4.2 |
| owner | string | Responsible person/team |
| project_code | string | Project or programme reference |
| created_at | datetime | Initial registration |
| status | enum | active / superseded / archived |

### 3.2 Document Version

| Field | Type | Description |
|-----|----|----|
| version_id | string | Unique version identifier |
| document_id | string | Parent document |
| version_label | string | e.g. A, B, C, 1.0 |
| source_path | string | Original file path |
| checksum | string | Integrity hash |
| created_at | datetime | Version timestamp |
| supersedes | version_id | Optional |

### 3.3 Artefact

| Field | Type | Description |
|-----|----|----|
| artefact_id | string | Unique ID |
| version_id | string | Source document version |
| artefact_type | enum | See §4.3 |
| storage_path | string | Object store reference |
| created_at | datetime | Generation timestamp |
| tool_name | string | Generating tool |
| tool_version | string | Tool version |
| confidence_level | enum | See §4.4 |

### 3.4 Chunk

| Field | Type | Description |
|-----|----|----|
| chunk_id | string | Stable identifier |
| artefact_id | string | Source artefact |
| chunk_type | enum | text / table / calc / summary |
| content | text | Chunk content |
| metadata | json | Section, page, etc. |

## 4. Enumerations

### 4.1 Document Type

ENGINEERING_REPORT  
DESIGN_SPECIFICATION  
CALCULATION  
PROPOSAL  
COSTING  
KNOWLEDGE_BASE  
DRAWING_2D  
MODEL_3D  
OTHER  

### 4.2 Authority Level

AUTHORITATIVE – Approved and current  
REFERENCE – Informative but not controlling  
DRAFT – Work-in-progress  
SUPERSEDED – Obsolete but retained  
ARCHIVED – Retained for record only  

### 4.3 Artefact Type

RAW_FILE  
EXTRACTED_TEXT  
TABLE_DATA  
IMAGE_PREVIEW  
MODEL_METADATA  
SUMMARY  
EMBEDDING  
INDEX_ENTRY  

### 4.4 Confidence Level

DECLARED – Explicitly stated in source  
CALCULATED – Computed from data  
INFERRED – Derived heuristically  
OCR_LOW – OCR with low confidence  

## 5. Metadata as a Contract

All modules MUST:
- read from metadata
- write metadata explicitly
- never infer authority implicitly
- log tool versions
