# Authority module

Purpose: enforce retrieval-level authority and access decisions before any search pipeline runs. The module is isolated from search engines and only talks to the metadata database.

Authority evaluation flow:
- Build an `AuthorityContext` containing the actor, roles, project_codes, and discipline for the request.
- Fetch documents and their `access_rules` from the metadata DB.
- Apply authority-level gating (only the canonical set is eligible) and require an explicit, fully matching access rule.
- Return only the document_ids the context may see; downstream retrieval must pre-filter on this set.

Enforcement at retrieval:
- Guarantees that lexical, vector, and hybrid searches never receive unauthorised document IDs.
- Avoids UI or LLM bypasses and keeps policy near the data boundary.
- UI- or LLM-side filtering is forbidden because it can be tampered with, and post-filtering leaks identifiers or snippets.
