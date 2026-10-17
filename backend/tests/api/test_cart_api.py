"""The menu and cart routes: status codes, the 409 codes the UI acts on, and isolation."""

from typing import Any

import httpx2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.preference import Preference
from app.users.models import User
from tests.api.conftest import login
from tests.orders.helpers import dish

CAFE = "bean-and-bloom"


async def latte(session: AsyncSession, milk: str, **extra: Any) -> dict[str, Any]:
    item_id, options = await dish(session, CAFE, "Latte")
    body = {"restaurant": CAFE, "item_id": item_id, "option_ids": [options["Small"], options[milk]]}
    return body | extra


async def allergic_to_dairy(session: AsyncSession, username: str) -> None:
    user_id = (await session.scalars(select(User.id).where(User.username == username))).one()
    session.add(Preference(user_id=user_id, kind="allergy", value="dairy"))
    await session.flush()


async def test_cart_and_menu_need_a_login(client: httpx2.AsyncClient) -> None:
    assert (await client.get("/api/cart")).status_code == 401
    assert (await client.get(f"/api/restaurants/{CAFE}/menu")).status_code == 401


async def test_the_menu_carries_this_guests_conflicts(
    seeded: AsyncSession, client: httpx2.AsyncClient
) -> None:
    await login(client, "menu_a")
    await allergic_to_dairy(seeded, "menu_a")
    body = (await client.get(f"/api/restaurants/{CAFE}/menu")).json()
    assert body["restaurant"]["slug"] == CAFE
    order = body["restaurant"]["categories"]
    positions = [order.index(i["category"]) for i in body["items"]]
    assert positions == sorted(positions)
    latte_card = next(i for i in body["items"] if i["name"] == "Latte")
    milks = {
        o["name"]: o["conflicts_with_guest"] for o in latte_card["option_groups"][1]["options"]
    }
    assert milks["Whole milk"] == ["dairy"] and milks["Oat milk"] == []
    karak = next(i for i in body["items"] if i["name"] == "Karak Chai")
    assert karak["conflicts_with_guest"] == ["dairy"]
    assert (await client.get("/api/restaurants/nowhere/menu")).status_code == 404


async def test_adding_and_the_409s_the_ui_answers(
    seeded: AsyncSession, client: httpx2.AsyncClient
) -> None:
    await login(client, "cart_api_a")
    await allergic_to_dairy(seeded, "cart_api_a")
    whole = await latte(seeded, "Whole milk")
    refused = await client.post("/api/cart/lines", json=whole)
    assert refused.status_code == 409
    assert refused.json()["detail"]["code"] == "conflict"
    assert refused.json()["detail"]["reasons"] == ["dairy"]
    added = await client.post("/api/cart/lines", json=whole | {"accepted_reasons": ["dairy"]})
    assert added.status_code == 200 and added.json()["item_count"] == 1

    sorbet, _ = await dish(seeded, "corner-table", "Mango Sorbet")
    elsewhere = {"restaurant": "corner-table", "item_id": sorbet}
    other = await client.post("/api/cart/lines", json=elsewhere)
    assert other.status_code == 409
    assert other.json()["detail"] | {"message": ""} == {
        "code": "other_restaurant",
        "message": "",
        "restaurant": "Bean & Bloom",
    }
    replaced = await client.post("/api/cart/lines", json=elsewhere | {"replace_cart": True})
    assert replaced.json()["restaurant"]["slug"] == "corner-table"


async def test_bad_bodies_are_422(seeded: AsyncSession, client: httpx2.AsyncClient) -> None:
    await login(client, "cart_api_b")
    oat = await latte(seeded, "Oat milk")
    no_milk = oat | {"option_ids": oat["option_ids"][:1]}
    invalid = await client.post("/api/cart/lines", json=no_milk)
    assert invalid.status_code == 422 and invalid.json()["detail"]["code"] == "invalid_choice"
    priced = await client.post("/api/cart/lines", json=oat | {"price_sar": "1.00"})
    assert priced.status_code == 422


async def test_changing_lines_and_isolation(
    seeded: AsyncSession, client: httpx2.AsyncClient, other_client: httpx2.AsyncClient
) -> None:
    await login(client, "cart_api_c")
    await login(other_client, "cart_api_d")
    cart = (await client.post("/api/cart/lines", json=await latte(seeded, "Oat milk"))).json()
    line = cart["lines"][0]["id"]
    assert (
        await other_client.patch(f"/api/cart/lines/{line}", json={"quantity": 5})
    ).status_code == 404
    assert (await other_client.delete(f"/api/cart/lines/{line}")).status_code == 404
    assert (await other_client.get("/api/cart")).json()["lines"] == []
    changed = await client.patch(f"/api/cart/lines/{line}", json={"quantity": 3})
    assert changed.json()["item_count"] == 3
    assert (await client.patch(f"/api/cart/lines/{line}", json={"quantity": 0})).status_code == 422
    assert (await client.delete(f"/api/cart/lines/{line}")).json()["lines"] == []
    await client.post("/api/cart/lines", json=await latte(seeded, "Oat milk"))
    assert (await client.delete("/api/cart")).json()["item_count"] == 0
