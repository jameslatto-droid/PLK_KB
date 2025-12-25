import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parents[3] / "env" / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


def _csv(name: str, default: str = "") -> List[str]:
    raw = os.getenv(name, default)
    return [v.strip() for v in raw.split(",") if v.strip()]


class Settings(BaseSettings):
    actor: str = os.getenv("PLK_ACTOR", "local_user")

    default_roles: List[str] = _csv("PLK_CONTEXT_ROLES", "viewer")
    default_project_codes: List[str] = _csv("PLK_CONTEXT_PROJECT_CODES", "")
    default_discipline: str = os.getenv("PLK_CONTEXT_DISCIPLINE", "general")
    default_classification: Optional[str] = os.getenv("PLK_CONTEXT_CLASSIFICATION")
    default_commercial_sensitivity: Optional[str] = os.getenv(
        "PLK_CONTEXT_COMMERCIAL_SENSITIVITY"
    )

    model_config = SettingsConfigDict(env_prefix="")


settings = Settings()
