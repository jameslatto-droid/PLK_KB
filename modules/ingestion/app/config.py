import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
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

    _minio_endpoint_raw: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_endpoint: str = (
        _minio_endpoint_raw if "://" in _minio_endpoint_raw else f"http://{_minio_endpoint_raw}"
    )
    minio_access_key: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "change_me")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "plk")
    
    # Stage 8: Extraction configuration
    enable_tier_2: bool = os.getenv("PLK_ENABLE_TIER_2", "false").lower() == "true"
    max_extract_mb: int = int(os.getenv("PLK_MAX_EXTRACT_MB", "100"))

    model_config = SettingsConfigDict(env_prefix="")


settings = Settings()
