"""Async engine and the per-request session dependency."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import Settings, get_settings


def engine_for(settings: Settings) -> AsyncEngine:
    if settings.app_env == "production":
        # Hosted Postgres (Netlify DB Free) sleeps when idle and has a monthly
        # compute cap. Pooled connections held open could keep it awake, so
        # production opens one connection per request and closes it after.
        return create_async_engine(settings.database_url, poolclass=NullPool)
    return create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=5)


@lru_cache
def get_engine() -> AsyncEngine:
    return engine_for(get_settings())


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request."""
    async with get_sessionmaker()() as session:
        yield session
