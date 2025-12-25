import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


_ENV_PATH = Path(__file__).resolve().parents[3] / "env" / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


class Settings(BaseSettings):
    environment: str = "development"

    opensearch_host: str = os.getenv("OPENSEARCH_HOST", "localhost")
    opensearch_port: int = int(os.getenv("OPENSEARCH_PORT", "9200"))
    opensearch_user: str = os.getenv("OPENSEARCH_USER", "admin")
    opensearch_password: str = os.getenv("OPENSEARCH_PASSWORD", "admin")
    opensearch_scheme: str = os.getenv("OPENSEARCH_SCHEME", "https")
    opensearch_index: str = os.getenv("OPENSEARCH_INDEX", "plk_chunks_v1")

    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY")
    qdrant_https: bool = os.getenv("QDRANT_HTTPS", "false").lower() == "true"
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "plk_chunks_v1")

    default_top_k: int = int(os.getenv("HYBRID_TOP_K", "10"))

    class Config:
        env_prefix = ""


settings = Settings()
