import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_PATH = Path(__file__).resolve().parents[3] / "env" / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


class Settings(BaseSettings):
    environment: str = "development"

    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY")
    qdrant_https: bool = os.getenv("QDRANT_HTTPS", "false").lower() == "true"

    collection_name: str = "plk_chunks_v1"
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    search_top_k: int = int(os.getenv("VECTOR_SEARCH_TOP_K", "5"))

    model_config = SettingsConfigDict(env_prefix="")


settings = Settings()
