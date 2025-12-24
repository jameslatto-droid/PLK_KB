from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"

    postgres_host: str
    postgres_db: str
    postgres_user: str
    postgres_password: str

    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str

    class Config:
        env_file = ".env"


settings = Settings()
