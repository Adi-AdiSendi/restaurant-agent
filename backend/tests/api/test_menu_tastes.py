"""The menu over HTTP carries soft taste notes for the logged-in guest."""

import httpx2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.preference import Preference
from app.users.models import User
from tests.api.conftest import login


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
