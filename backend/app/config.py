"""Application settings, read from the environment (and `.env` locally)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


def to_asyncpg_url(url: str) -> str:
    """Rewrite plain Postgres URLs (as Railway provides them) for the asyncpg driver."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url.removeprefix(prefix)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/restaurant"
    openai_api_key: str = ""
    openai_model: str = "gpt-6-luna"
    session_secret: str = ""
    frontend_dist: Path = REPO_ROOT / "frontend" / "dist"

    @field_validator("database_url")
    @classmethod
    def _use_asyncpg(cls, value: str) -> str:
        return to_asyncpg_url(value)

    @model_validator(mode="after")
    def _require_session_secret_in_production(self) -> Self:
        if self.app_env == "production" and len(self.session_secret) < 32:
            raise ValueError("SESSION_SECRET must be set (32+ characters) in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
