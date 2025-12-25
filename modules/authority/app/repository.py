"""Data access for authority evaluation (metadata DB only)."""

from typing import Dict, List, Optional

from modules.metadata.app.db import connection_cursor  # type: ignore


def fetch_documents_with_rules(document_ids: Optional[List[str]] = None) -> List[Dict]:
    """
    Return raw document rows joined to access_rules.

    No policy filtering occurs here; callers must apply authority rules.
    If document_ids is provided, limit the query to that set.
    """
    query = (
        """
        SELECT
            d.document_id,
            d.authority_level,
            d.project_code AS document_project_code,
            ar.rule_id,
            ar.project_code AS rule_project_code,
            ar.discipline,
            ar.classification,
            ar.commercial_sensitivity,
            ar.allowed_roles
        FROM documents d
        LEFT JOIN access_rules ar ON ar.document_id = d.document_id
        """
    )
    params: tuple = ()
    if document_ids:
        placeholders = ",".join(["%s"] * len(document_ids))
        query += f" WHERE d.document_id IN ({placeholders})"
        params = tuple(document_ids)

    with connection_cursor(dict_cursor=True) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
