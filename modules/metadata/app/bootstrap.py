from pathlib import Path

from modules.metadata.app.db import connection_cursor


def ensure_schema() -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")
    with connection_cursor() as cur:
        cur.execute(sql)


def main() -> None:
    ensure_schema()


if __name__ == "__main__":
    main()
