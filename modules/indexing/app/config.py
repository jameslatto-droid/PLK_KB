from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"

    opensearch_host: str = "opensearch"
    opensearch_port: int = 9200

    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333

    class Config:
        env_file = ".env"


settings = Settings()
