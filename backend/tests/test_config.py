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
        (
            "postgresql://u:p@h/db?sslmode=require&channel_binding=require",
            "postgresql+asyncpg://u:p@h/db?ssl=require",
        ),
        ("postgres://u:p@h/db?ssl=require", "postgresql+asyncpg://u:p@h/db?ssl=require"),
        ("  postgresql://u:p@h/db \t", "postgresql+asyncpg://u:p@h/db"),
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


def test_settings_rewrite_hosted_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.host/app?sslmode=require")
    assert (
        SettingsWithoutEnvFile().database_url == "postgresql+asyncpg://u:p@db.host/app?ssl=require"
    )


@pytest.mark.parametrize("seconds", ["0", "26", "30"])
def test_turn_deadline_must_fit_under_the_proxy_limit(
    monkeypatch: pytest.MonkeyPatch, seconds: str
) -> None:
    monkeypatch.setenv("TURN_DEADLINE_SECONDS", seconds)
    with pytest.raises(ValidationError):
        SettingsWithoutEnvFile()
