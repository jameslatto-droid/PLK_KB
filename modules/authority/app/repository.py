"""Data access for authority evaluation (metadata DB only)."""

from typing import Dict, List

from modules.metadata.app.db import connection_cursor  # type: ignore


def fetch_documents_with_rules() -> List[Dict]:
    """
    Return raw document rows joined to access_rules.

    No policy filtering occurs here; callers must apply authority rules.
    """
    query = """
        SELECT
            d.document_id,
            d.authority_level,
            d.project_code AS document_project_code,
            ar.rule_id,
            ar.project_code AS rule_project_code,
            ar.discipline,
            ar.classification,
            ar.allowed_roles
        FROM documents d
        LEFT JOIN access_rules ar ON ar.document_id = d.document_id
    """
    with connection_cursor(dict_cursor=True) as cur:
        cur.execute(query)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
