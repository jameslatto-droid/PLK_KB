import contextlib
import psycopg2
from psycopg2.extras import RealDictCursor

from .config import settings


def get_connection():
    """Create a new database connection using environment-backed settings."""
    return psycopg2.connect(
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
    )


@contextlib.contextmanager
def connection_cursor(*, dict_cursor: bool = False):
    """Context manager yielding a cursor with automatic commit/close."""
    conn = get_connection()
    try:
        cursor_factory = RealDictCursor if dict_cursor else None
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            yield cur
        conn.commit()
    finally:
        conn.close()
