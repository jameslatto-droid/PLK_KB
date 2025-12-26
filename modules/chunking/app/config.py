import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_PATH = Path(__file__).resolve().parents[3] / "env" / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


class Settings(BaseSettings):
    environment: str = "development"

    max_chunk_chars: int = 700

    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_db: str = os.getenv("POSTGRES_DB", "plk_metadata")
    postgres_user: str = os.getenv("POSTGRES_USER", "plk_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "change_me")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))

    _minio_endpoint_raw: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_endpoint: str = (
        _minio_endpoint_raw if "://" in _minio_endpoint_raw else f"http://{_minio_endpoint_raw}"
    )
    minio_access_key: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "change_me")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "plk")

    model_config = SettingsConfigDict(env_prefix="")


settings = Settings()
