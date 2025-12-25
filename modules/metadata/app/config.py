import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parents[3] / "env" / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


@dataclass
class Settings:
    db_name: str = os.getenv("POSTGRES_DB", "plk_metadata")
    db_user: str = os.getenv("POSTGRES_USER", "plk_user")
    db_password: str = os.getenv("POSTGRES_PASSWORD", "change_me")
    db_host: str = os.getenv("POSTGRES_HOST", "localhost")
    db_port: int = int(os.getenv("POSTGRES_PORT", "5432"))


settings = Settings()
