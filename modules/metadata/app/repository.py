from typing import List, Optional, Dict, Any
from psycopg2.extras import Json
from .db import connection_cursor
from .models import (
    Document,
    DocumentVersion,
    Artefact,
    Chunk,
    AccessRule,
    AuditLog,
)



class DocumentRepository:
    @staticmethod
    def insert(doc: Document) -> None:
        with connection_cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (
                    document_id,
                    title,
                    document_type,
                    authority_level,
                    owner,
                    project_code,
                    status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) DO NOTHING
                """,
                (
                    doc.document_id,
                    doc.title,
                    doc.document_type,
                    doc.authority_level,
                    doc.owner,
                    doc.project_code,
                    doc.status,
                ),
            )

    @staticmethod
    def get(document_id: str) -> Optional[Dict[str, Any]]:
        with connection_cursor(dict_cursor=True) as cur:
            cur.execute(
                """
                SELECT
                    document_id,
                    title,
                    document_type,
                    authority_level,
                    owner,
                    project_code,
                    status,
                    created_at
                FROM documents
                WHERE document_id = %s
                """,
                (document_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_status(document_id: str, status: str) -> int:
        with connection_cursor() as cur:
            cur.execute(
                """
                UPDATE documents
                SET status = %s
                WHERE document_id = %s
                """,
                (status, document_id),
            )
            return cur.rowcount


class DocumentVersionRepository:
    @staticmethod
    def insert(version: DocumentVersion) -> None:
        with connection_cursor() as cur:
            cur.execute(
                """
                INSERT INTO document_versions (
                    version_id,
                    document_id,
                    version_label,
                    source_path,
                    checksum,
                    supersedes
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (version_id) DO NOTHING
                """,
                (
                    version.version_id,
                    version.document_id,
                    version.version_label,
                    version.source_path,
                    version.checksum,
                    version.supersedes,
                ),
            )

    @staticmethod
    def get(version_id: str) -> Optional[Dict[str, Any]]:
        with connection_cursor(dict_cursor=True) as cur:
            cur.execute(
                """
                SELECT
                    version_id,
                    document_id,
                    version_label,
                    source_path,
                    checksum,
                    supersedes,
                    created_at
                FROM document_versions
                WHERE version_id = %s
                """,
                (version_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


class ArtefactRepository:
    @staticmethod
    def insert(artefact: Artefact) -> None:
        with connection_cursor() as cur:
            cur.execute(
                """
                INSERT INTO artefacts (
                    artefact_id,
                    version_id,
                    artefact_type,
                    storage_path,
                    tool_name,
                    tool_version,
                    confidence_level
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (artefact_id) DO NOTHING
                """,
                (
                    artefact.artefact_id,
                    artefact.version_id,
                    artefact.artefact_type,
                    artefact.storage_path,
                    artefact.tool_name,
                    artefact.tool_version,
                    artefact.confidence_level,
                ),
            )

    @staticmethod
    def get_by_version(version_id: str) -> List[Dict[str, Any]]:
        with connection_cursor(dict_cursor=True) as cur:
            cur.execute(
                """
                SELECT
                    artefact_id,
                    version_id,
                    artefact_type,
                    storage_path,
                    tool_name,
                    tool_version,
                    confidence_level,
                    created_at
                FROM artefacts
                WHERE version_id = %s
                ORDER BY created_at DESC
                """,
                (version_id,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get(artefact_id: str) -> Optional[Dict[str, Any]]:
        with connection_cursor(dict_cursor=True) as cur:
            cur.execute(
                """
                SELECT
                    artefact_id,
                    version_id,
                    artefact_type,
                    storage_path,
                    tool_name,
                    tool_version,
                    confidence_level,
                    created_at
                FROM artefacts
                WHERE artefact_id = %s
                """,
                (artefact_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


class ChunkRepository:
    @staticmethod
    def insert(chunk: Chunk) -> None:
        with connection_cursor() as cur:
            cur.execute(
                """
                INSERT INTO chunks (
                    chunk_id,
                    artefact_id,
                    chunk_type,
                    content,
                    metadata
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO NOTHING
                """,
                (
                    chunk.chunk_id,
                    chunk.artefact_id,
                    chunk.chunk_type,
                    chunk.content,
                    Json(chunk.metadata),
                ),
            )

    @staticmethod
    def get_by_artefact(artefact_id: str) -> List[Dict[str, Any]]:
        with connection_cursor(dict_cursor=True) as cur:
            cur.execute(
                """
                SELECT
                    chunk_id,
                    artefact_id,
                    chunk_type,
                    content,
                    metadata
                FROM chunks
                WHERE artefact_id = %s
                ORDER BY chunk_id
                """,
                (artefact_id,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def list_all_with_lineage() -> List[Dict[str, Any]]:
        """Fetch all chunks with document_id resolved via artefact -> version."""
        with connection_cursor(dict_cursor=True) as cur:
            cur.execute(
                """
                SELECT
                    c.chunk_id,
                    c.artefact_id,
                    c.chunk_type,
                    c.content,
                    c.metadata,
                    dv.document_id
                FROM chunks c
                JOIN artefacts a ON c.artefact_id = a.artefact_id
                JOIN document_versions dv ON a.version_id = dv.version_id
                ORDER BY c.chunk_id
                """
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]


class AccessRuleRepository:
    @staticmethod
    def insert(rule: AccessRule) -> None:
        with connection_cursor() as cur:
            cur.execute(
                """
                INSERT INTO access_rules (
                    document_id,
                    project_code,
                    discipline,
                    classification,
                    commercial_sensitivity,
                    allowed_roles
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING rule_id
                """,
                (
                    rule.document_id,
                    rule.project_code,
                    rule.discipline,
                    rule.classification,
                    rule.commercial_sensitivity,
                    rule.allowed_roles,
                ),
            )
            returned = cur.fetchone()
            if returned:
                rule.rule_id = returned[0]

    @staticmethod
    def get_by_document(document_id: str) -> List[Dict[str, Any]]:
        with connection_cursor(dict_cursor=True) as cur:
            cur.execute(
                """
                SELECT
                    rule_id,
                    document_id,
                    project_code,
                    discipline,
                    classification,
                    commercial_sensitivity,
                    allowed_roles,
                    created_at
                FROM access_rules
                WHERE document_id = %s
                ORDER BY rule_id
                """,
                (document_id,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]


class AuditLogRepository:
    @staticmethod
    def insert_event(event: AuditLog) -> None:
        with connection_cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_log (
                    actor,
                    action,
                    document_id,
                    version_id,
                    model_version,
                    index_version,
                    details
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING audit_id
                """,
                (
                    event.actor,
                    event.action,
                    event.document_id,
                    event.version_id,
                    event.model_version,
                    event.index_version,
                    Json(event.details) if event.details is not None else None,
                ),
            )
            returned = cur.fetchone()
            if returned:
                event.audit_id = returned[0]

    @staticmethod
    def query_recent(limit: int = 50) -> List[Dict[str, Any]]:
        with connection_cursor(dict_cursor=True) as cur:
            cur.execute(
                """
                SELECT
                    audit_id,
                    actor,
                    action,
                    document_id,
                    version_id,
                    model_version,
                    index_version,
                    details,
                    created_at
                FROM audit_log
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
