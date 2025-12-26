# Phase 3 Status – Control Plane & Deterministic Retrieval

## Completed
- Step 1: Postgres + schema validation
- Step 2: Metadata access layer (tested)
- Step 3: Minimal ingestion (TXT → artefact)
- Step 4: Deterministic chunking (stable IDs)
- Step 5: Lexical indexing (OpenSearch)

## Current State
- All deterministic layers operational
- OpenSearch index: plk_chunks_v1
- One demo document successfully ingested, chunked, indexed
- Rebuilds are deterministic and repeatable

## Explicitly Deferred
- PDF ingestion
- OCR
- CAD / drawings
- Vector embeddings
- Hybrid search
- User-facing API / UI

## Next Logical Steps
- Phase 3 Step 6: Vector indexing (Qdrant + embeddings)
- OR hardening/docs
- OR API / portal layer
