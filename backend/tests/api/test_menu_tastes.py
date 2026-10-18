"""The menu over HTTP carries soft taste notes for the logged-in guest."""

import httpx2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.preference import Preference
from app.menu import clock
from app.users.models import User
from tests.api.conftest import login
from tests.api.test_cart_api import latte as latte_line


async def test_the_menu_carries_notes_for_the_logged_in_guest(
    seeded: AsyncSession, client: httpx2.AsyncClient
) -> None:
    await login(client, "taste_api")
    user_id = await seeded.scalar(select(User.id).where(User.username == "taste_api"))
    seeded.add(Preference(user_id=user_id, kind="budget", value="20.00"))
    await seeded.flush()
    items = (await client.get("/api/restaurants/bean-and-bloom/menu")).json()["items"]
    notes = {i["name"]: i["taste_notes"] for i in items}
    assert notes["Espresso"] == []
    assert "over your 20.00 SAR budget" in notes["San Sebastian Cheesecake"]


async def test_today_counts_only_the_guests_own_orders(
    seeded: AsyncSession, client: httpx2.AsyncClient, other_client: httpx2.AsyncClient
) -> None:
    await login(client, "today_me")
    await login(other_client, "today_other")
    latte = await latte_line(seeded, "Oat milk")
    await other_client.post("/api/cart/lines", json=latte)
    await other_client.post("/api/orders", json={"fulfilment": "pickup"})
    body = (await client.get("/api/preferences/today")).json()
    assert body["kcal"] == 0 and body["weekday"] == clock.weekday()
    await client.post("/api/cart/lines", json=latte)
    await client.post("/api/orders", json={"fulfilment": "pickup"})
    assert (await client.get("/api/preferences/today")).json()["kcal"] == 150 + 20
