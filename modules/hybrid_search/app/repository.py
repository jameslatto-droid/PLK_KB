"""Read-only helpers for chunk retrieval."""

from typing import Dict, Optional

from modules.metadata.app.db import connection_cursor  # type: ignore


def get_chunk_with_document(chunk_id: str) -> Optional[Dict]:
    query = (
        """
        SELECT c.chunk_id, c.content, c.artefact_id, dv.document_id
        FROM chunks c
        JOIN artefacts a ON c.artefact_id = a.artefact_id
        JOIN document_versions dv ON a.version_id = dv.version_id
        WHERE c.chunk_id = %s
        """
    )
    with connection_cursor(dict_cursor=True) as cur:
        cur.execute(query, (chunk_id,))
        row = cur.fetchone()
        return dict(row) if row else None
