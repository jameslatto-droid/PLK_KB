# Vector Indexing

Phase 3 Step 6 – Qdrant-based semantic indexing for PLK_KB chunks.

## Requirements
- Python 3.11+
- sentence-transformers (default model: `all-MiniLM-L6-v2`)
- qdrant-client (HTTP)
- Access to Postgres metadata DB (read-only) and running Qdrant instance

Install dependencies:

```
pip install -r modules/vector_indexing/requirements.txt
```

## Environment
Values are loaded from `env/.env`:
- `QDRANT_HOST` (default: `localhost`)
- `QDRANT_PORT` (default: `6333`)
- `QDRANT_API_KEY` (optional)
- `QDRANT_HTTPS` (`true` / `false`, default `false`)
- `EMBEDDING_MODEL` (default: `all-MiniLM-L6-v2`)
- `VECTOR_SEARCH_TOP_K` (default: `5`)

## Commands
Rebuild vector index deterministically (drops and recreates collection `plk_chunks_v1`):

```
python -m modules.vector_indexing.app.indexer rebuild
```

Run semantic search:

```
python -m modules.vector_indexing.app.search "query text"
```

Outputs list Qdrant point id, document id, chunk index, character span, and score.
