from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"

    max_chunk_chars: int = 2000
    min_chunk_chars: int = 300

    class Config:
        env_file = ".env"


settings = Settings()
