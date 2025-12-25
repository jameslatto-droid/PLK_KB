# Hybrid Search

Phase 3 Step 7 – combines lexical (OpenSearch) and semantic (Qdrant) results.

## Behavior
- Queries OpenSearch and Qdrant independently for the same query
- Normalizes both score sets to [0,1]
- `final_score = 0.5 * lexical_norm + 0.5 * semantic_norm`
- Merges by `chunk_id`; missing scores treated as 0
- Fills missing content/document/artefact fields from Postgres metadata

## CLI
From repo root (ensure env/.venv is active and `PYTHONPATH` points to repo root):

```
python -m modules.hybrid_search.app.cli "your query" --size 10
```

## Output fields
- chunk_id
- document_id
- artefact_id
- snippet (first 200 chars)
- lexical_score (raw from OpenSearch)
- semantic_score (raw from Qdrant)
- final_score (combined normalized)

## Configuration (env/.env)
- OPENSEARCH_HOST, OPENSEARCH_PORT, OPENSEARCH_USER, OPENSEARCH_PASSWORD, OPENSEARCH_SCHEME
- OPENSEARCH_INDEX (default `plk_chunks_v1`)
- QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY, QDRANT_HTTPS
- QDRANT_COLLECTION (default `plk_chunks_v1`)
- HYBRID_TOP_K (default `10`)
