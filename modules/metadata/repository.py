import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor


DEFAULT_DB_NAME = os.getenv("METADATA_DB_NAME", "plk_metadata")
DEFAULT_DB_USER = os.getenv("METADATA_DB_USER", "plk_user")
DEFAULT_DB_PASSWORD = os.getenv("METADATA_DB_PASSWORD", "change_me")
DEFAULT_DB_HOST = os.getenv("METADATA_DB_HOST", "localhost")
DEFAULT_DB_PORT = int(os.getenv("METADATA_DB_PORT", "5432"))


def get_connection(
    *,
    dbname: str = DEFAULT_DB_NAME,
    user: str = DEFAULT_DB_USER,
    password: str = DEFAULT_DB_PASSWORD,
    host: str = DEFAULT_DB_HOST,
    port: int = DEFAULT_DB_PORT,
):
    """Create a new database connection using psycopg2."""
    return psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )


def create_document(
    *,
    document_id: str,
    title: str,
    document_type: str,
    authority_level: str,
    owner: Optional[str] = None,
    project_code: Optional[str] = None,
    status: str = "active",
    connection=None,
) -> None:
    """Insert a document row matching the documents table definition."""
    close_conn = connection is None
    conn = connection or get_connection()
    try:
        with conn.cursor() as cur:
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
                """,
                (
                    document_id,
                    title,
                    document_type,
                    authority_level,
                    owner,
                    project_code,
                    status,
                ),
            )
        conn.commit()
    finally:
        if close_conn:
            conn.close()


def get_document(*, document_id: str, connection=None) -> Optional[Dict[str, Any]]:
    """Fetch a single document by primary key."""
    close_conn = connection is None
    conn = connection or get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
    finally:
        if close_conn:
            conn.close()


def list_documents(*, status: Optional[str] = None, connection=None) -> List[Dict[str, Any]]:
    """List documents with optional status filter."""
    close_conn = connection is None
    conn = connection or get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if status:
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
                    WHERE status = %s
                    ORDER BY created_at DESC
                    """,
                    (status,),
                )
            else:
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
                    ORDER BY created_at DESC
                    """
                )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        if close_conn:
            conn.close()


def update_document(
    *,
    document_id: str,
    title: Optional[str] = None,
    document_type: Optional[str] = None,
    authority_level: Optional[str] = None,
    owner: Optional[str] = None,
    project_code: Optional[str] = None,
    status: Optional[str] = None,
    connection=None,
) -> int:
    """Update allowed columns on documents; returns rows affected."""
    fields = []
    values = []
    if title is not None:
        fields.append("title = %s")
        values.append(title)
    if document_type is not None:
        fields.append("document_type = %s")
        values.append(document_type)
    if authority_level is not None:
        fields.append("authority_level = %s")
        values.append(authority_level)
    if owner is not None:
        fields.append("owner = %s")
        values.append(owner)
    if project_code is not None:
        fields.append("project_code = %s")
        values.append(project_code)
    if status is not None:
        fields.append("status = %s")
        values.append(status)

    if not fields:
        return 0

    values.append(document_id)

    close_conn = connection is None
    conn = connection or get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE documents
                SET {', '.join(fields)}
                WHERE document_id = %s
                """,
                tuple(values),
            )
            rowcount = cur.rowcount
        conn.commit()
        return rowcount
    finally:
        if close_conn:
            conn.close()


def delete_document(*, document_id: str, connection=None) -> int:
    """Hard delete a document row by primary key; returns rows affected."""
    close_conn = connection is None
    conn = connection or get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM documents
                WHERE document_id = %s
                """,
                (document_id,),
            )
            rowcount = cur.rowcount
        conn.commit()
        return rowcount
    finally:
        if close_conn:
            conn.close()
