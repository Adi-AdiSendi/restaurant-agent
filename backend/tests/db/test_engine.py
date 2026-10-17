"""Needs the Postgres from docker compose (or the CI service)."""

from sqlalchemy import text
from sqlalchemy.pool import NullPool

from app.config import Settings
from app.db.engine import engine_for, get_session


async def test_session_reaches_postgres() -> None:
    async for session in get_session():
        result = await session.execute(text("select version()"))
        assert result.scalar_one().startswith("PostgreSQL 16")


def test_production_keeps_no_idle_connections() -> None:
    production = Settings(app_env="production", session_secret="x" * 32)
    assert isinstance(engine_for(production).pool, NullPool)
    assert not isinstance(engine_for(Settings(app_env="test")).pool, NullPool)
