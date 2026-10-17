import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from app.config import Settings, to_asyncpg_url


class SettingsWithoutEnvFile(Settings):
    """Ignores the developer's .env so local values cannot change results."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgres://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
        ("postgresql://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
        ("postgresql+asyncpg://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
    ],
)
def test_to_asyncpg_url(given: str, expected: str) -> None:
    assert to_asyncpg_url(given) == expected


def test_production_requires_a_long_session_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    for secret in ("", "short"):
        monkeypatch.setenv("SESSION_SECRET", secret)
        with pytest.raises(ValidationError):
            SettingsWithoutEnvFile()
    monkeypatch.setenv("SESSION_SECRET", "x" * 32)
    assert SettingsWithoutEnvFile().app_env == "production"


def test_development_allows_an_empty_session_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SESSION_SECRET", "")
    assert SettingsWithoutEnvFile().session_secret == ""


def test_settings_rewrite_railway_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@railway:5432/railway")
    assert SettingsWithoutEnvFile().database_url == "postgresql+asyncpg://u:p@railway:5432/railway"
