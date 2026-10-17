"""Shared fixtures. DB tests use the docker compose Postgres (or the CI service)."""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_engine
from app.users.models import User
from scripts.seed_menu import load_menu, seed_menu


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """A session inside an outer transaction that is always rolled back."""
    async with get_engine().connect() as connection:
        outer = await connection.begin()
        db = AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        try:
            yield db
        finally:
            await db.close()
            await outer.rollback()


@pytest.fixture
async def seeded(session: AsyncSession) -> AsyncSession:
    await seed_menu(session, load_menu())
    return session


async def make_user(session: AsyncSession, username: str) -> int:
    """A user without argon2 cost; use the login API when the PIN matters."""
    user = User(username=username, pin_hash="not-a-real-hash")
    session.add(user)
    await session.flush()
    return user.id
