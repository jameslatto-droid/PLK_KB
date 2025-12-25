# Metadata Access Layer

Thin, explicit client for the metadata control-plane database (`plk_metadata`). No business logic; only 1:1 SQL mapped to docs/07_database_schema.md.

## Components
- app/config.py – loads POSTGRES_* from env/.env (defaults: localhost/plk_metadata/plk_user/change_me).
- app/db.py – psycopg2 connection factory.
- app/models.py – Pydantic models mirroring each table.
- app/repository.py – explicit parameterised CRUD helpers per table.
- tests/test_smoke.py – inserts + reads roundtrip and cleans up.

## Usage (local dev)
```bash
pip install -r requirements.txt
pytest modules/metadata/tests -q
```

Environment variables (optionally via env/.env):
- POSTGRES_HOST (default: localhost)
- POSTGRES_DB (default: plk_metadata)
- POSTGRES_USER (default: plk_user)
- POSTGRES_PASSWORD (default: change_me)
- POSTGRES_PORT (default: 5432)
