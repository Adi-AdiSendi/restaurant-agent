"""Locks across real, committed transactions. The other DB tests share one rolled-back
transaction, so they cannot show two requests waiting on each other."""

import asyncio
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import delete, func, select, text

from app.db.engine import get_sessionmaker
from app.menu.constraints import NO_CONSTRAINTS
from app.orders.cart_add import add_line
from app.orders.checkout import place_order
from app.orders.errors import EmptyCart
from app.orders.models import Order
from app.orders.schemas import NewLine, OrderOut
from app.users.models import User
from app.users.service import lock_user
from scripts.seed_menu import load_restaurants, seed_menus
from tests.orders.helpers import dish

NAME = "lock_test_user"


@pytest.fixture
async def user_id() -> AsyncIterator[int]:
    maker = get_sessionmaker()
    async with maker() as session, session.begin():
        await seed_menus(session, load_restaurants())  # idempotent, as on every deploy
        await session.execute(delete(User).where(User.username == NAME))
        user = User(username=NAME, pin_hash="not-a-real-hash")
        session.add(user)
        await session.flush()
        new_id = user.id
    try:
        yield new_id
    finally:
        async with maker() as session, session.begin():
            await session.execute(delete(User).where(User.id == new_id))


async def oat_latte() -> NewLine:
    async with get_sessionmaker()() as session:
        item_id, options = await dish(session, "bean-and-bloom", "Latte")
    return NewLine(item_id=item_id, option_ids=[options["Small"], options["Oat milk"]])


async def test_a_chat_turn_does_not_block_the_cart_or_checkout(user_id: int) -> None:
    """A turn holds the user row for its whole run (up to 22 s); ordering must not wait."""
    maker = get_sessionmaker()
    line = await oat_latte()
    async with maker() as chat, chat.begin(), maker() as shop, shop.begin():
        await lock_user(chat, user_id)
        await shop.execute(text("SET LOCAL lock_timeout = '2s'"))
        await add_line(shop, user_id, "bean-and-bloom", line, NO_CONSTRAINTS)
        order = await place_order(shop, user_id, "pickup", NO_CONSTRAINTS)
        assert order.total_sar > 0
        await shop.rollback()
        await chat.rollback()


async def test_two_checkouts_at_once_place_one_order(user_id: int) -> None:
    maker = get_sessionmaker()
    async with maker() as session, session.begin():
        await add_line(session, user_id, "bean-and-bloom", await oat_latte(), NO_CONSTRAINTS)

    async def checkout() -> OrderOut:
        async with maker() as session, session.begin():
            return await place_order(session, user_id, "pickup", NO_CONSTRAINTS)

    results = await asyncio.gather(checkout(), checkout(), return_exceptions=True)
    assert sorted(type(r).__name__ for r in results) == ["EmptyCart", "OrderOut"]
    assert any(isinstance(r, EmptyCart) for r in results)
    async with maker() as session:
        count = select(func.count()).select_from(Order).where(Order.user_id == user_id)
        assert await session.scalar(count) == 1
