"""Application settings, read from the environment (and `.env` locally)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


def to_asyncpg_url(url: str) -> str:
    """Rewrite plain Postgres URLs (as hosted databases provide them) for asyncpg.

    asyncpg takes `ssl=` instead of libpq's `sslmode=` and rejects `channel_binding`.
    Spaces around a pasted value are dropped.
    """
    url = url.strip()
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = "postgresql+asyncpg://" + url.removeprefix(prefix)
    parts = urlsplit(url)
    if not parts.query:
        return url
    params = [
        ("ssl" if key == "sslmode" else key, value)
        for key, value in parse_qsl(parts.query)
        if key != "channel_binding"
    ]
    return urlunsplit(parts._replace(query=urlencode(params)))


class Settings(BaseSettings):
    # Values pasted into a host dashboard often carry stray spaces; an API key
    # with one fails every OpenAI call.
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", extra="ignore", str_strip_whitespace=True
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/restaurant"
    openai_api_key: str = ""
    openai_model: str = "gpt-6-luna"
    session_secret: str = ""
    # Seconds for one chat turn. Must stay under the Netlify proxy's fixed 26 s.
    turn_deadline_seconds: float = Field(default=22.0, gt=0, lt=26)
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
