from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PLK_KB API"
    environment: str = "development"

    postgres_host: str
    postgres_db: str
    postgres_user: str
    postgres_password: str

    class Config:
        env_file = ".env"


settings = Settings()
