---
type: summary
project: CISEC
project-code: P-2024-001
status: active
stage: 2
tags: [cisec, architecture, modular]
---

# Target Architecture & Core Modules

## 1. Architectural Overview

PLK_KB is a **modular, on-prem knowledge platform** deployed initially on a single workstation using containerised services.

The architecture enforces strict separation between:

- data storage
- processing pipelines
- indexing
- retrieval logic
- reasoning (LLMs)

---

## 2. Core Architectural Rules

1. Raw files are immutable
2. Derived artefacts are explicit
3. Indexes are disposable
4. Authority is metadata-driven
5. LLMs never access raw files
6. All answers must be traceable

---

## 3. Core Modules

### 3.1 Storage
Stores raw and derived artefacts using object storage semantics.

### 3.2 Metadata & Governance
Maintains document identity, versioning, authority, permissions, and lineage.

### 3.3 Ingestion
Extracts text, tables, metadata, previews, and structured facts from source files.

### 3.4 Normalisation & Chunking
Transforms extracted content into stable, retrievable knowledge units.

### 3.5 Indexing
Maintains lexical and semantic indexes derived from chunks and metadata.

### 3.6 Retrieval
Performs metadata-filtered hybrid retrieval and reranking.

### 3.7 LLM Integration
Consumes curated context for summarisation and synthesis only.

### 3.8 Analysis & Compilation
Generates structured analytical outputs from the corpus.

### 3.9 API Layer
Exposes platform capabilities to a future user portal.

---

## 4. Deployment Model

- Fully on-prem
- Container-based
- No mandatory external connectivity
- Designed for incremental scale-out
