# Authority Module (Stage 5)

Enforces authority & access decisions before any retrieval occurs. The module is isolated from search engines and talks only to the metadata database.

Key rules:
- Allowed authority levels: AUTHORITATIVE, REFERENCE, DRAFT, EXTERNAL. Anything else is rejected.
- Access rules evaluate with OR semantics; a document is allowed if any rule fully matches.
- Missing access rules => deny by default.
- Matching requires project_code, discipline, classification, commercial_sensitivity, and role intersection when those fields are present on the rule.

APIs:
- `evaluate_document_access(context, document_id, query_id=...) -> AccessDecision` (allows/denies + reasons + matched_rule_ids)
- `get_allowed_document_ids(context, query_id=...) -> set[str]` (pre-filter for search paths)
- `validate_authority_level(level)` (fail-fast validation for ingestion)
- `load_default_context()` (builds context from env defaults: PLK_CONTEXT_* and PLK_ACTOR)

CLI examples (from repo root):
- Validate level: `python -m modules.authority.app.cli validate AUTHORITATIVE`
- Evaluate doc: `python -m modules.authority.app.cli eval-doc DEMO-TXT-001 --roles viewer --projects P1`
- Batch allowed: `python -m modules.authority.app.cli eval-batch --roles viewer --projects P1`

Env defaults:
- `PLK_ACTOR` (default local_user)
- `PLK_CONTEXT_ROLES` (csv, default viewer)
- `PLK_CONTEXT_PROJECT_CODES` (csv, optional)
- `PLK_CONTEXT_DISCIPLINE` (default general)
- `PLK_CONTEXT_CLASSIFICATION` (optional)
- `PLK_CONTEXT_COMMERCIAL_SENSITIVITY` (optional)
