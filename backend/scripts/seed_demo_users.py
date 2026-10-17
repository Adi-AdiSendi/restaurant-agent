"""Reset the two demo accounts reviewers use. Safe to run on every deploy.

Each run deletes the demo users (their chats and memory go with them) and
recreates them, so whatever a reviewer changed does not pile up.

Usage: uv run python -m scripts.seed_demo_users
"""

import asyncio
import logging

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_engine, get_sessionmaker
from app.memory.operations import Operation
from app.memory.supersede import apply_operations
from app.users.models import User
from app.users.service import Credentials, login_or_register

logger = logging.getLogger(__name__)


def _add(kind: str, value: str) -> Operation:
    return Operation.model_validate({"op": "add", "kind": kind, "value": value})


# Each inner list is applied in order, like facts learned over several chats.
# demo_alice once liked hot food and later asked for mild, so "hot" shows as replaced.
DEMO_USERS: dict[str, tuple[str, list[list[Operation]]]] = {
    "demo_alice": (
        "1234",
        [
            [_add("allergy", "peanut"), _add("spice", "hot")],
            [_add("diet", "vegetarian")],
            [_add("spice", "mild")],
        ],
    ),
    "demo_bob": ("5678", []),
}


async def seed_demo_users(session: AsyncSession) -> None:
    await session.execute(delete(User).where(User.username.in_(DEMO_USERS)))
    for username, (pin, steps) in DEMO_USERS.items():
        result = await login_or_register(session, Credentials(username=username, pin=pin))
        for ops in steps:
            await apply_operations(session, result.user_id, ops, source_message_id=None)


async def main() -> None:
    async with get_sessionmaker()() as session, session.begin():
        await seed_demo_users(session)
    await get_engine().dispose()
    logger.info("demo_users_seeded users=%d", len(DEMO_USERS))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    asyncio.run(main())
