import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parents[3] / "env" / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


class Settings(BaseSettings):
    environment: str = "development"

    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_db: str = os.getenv("POSTGRES_DB", "plk_metadata")
    postgres_user: str = os.getenv("POSTGRES_USER", "plk_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "change_me")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))

    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "change_me")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "plk")

    class Config:
        env_prefix = ""


settings = Settings()
