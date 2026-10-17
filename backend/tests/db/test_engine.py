"""Needs the Postgres from docker compose (or the CI service)."""

from sqlalchemy import text

from app.db.engine import get_session


async def test_session_reaches_postgres() -> None:
    async for session in get_session():
        result = await session.execute(text("select version()"))
        assert result.scalar_one().startswith("PostgreSQL 16")
