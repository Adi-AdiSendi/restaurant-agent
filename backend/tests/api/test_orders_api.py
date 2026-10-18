"""Placing and reading orders over HTTP, and that one guest never sees another's."""

import httpx2
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api.conftest import login
from tests.api.test_cart_api import CAFE, allergic_to_dairy, latte


async def test_place_list_and_read_an_order(
    seeded: AsyncSession, client: httpx2.AsyncClient
) -> None:
    await login(client, "ord_api_a")
    await client.post("/api/cart/lines", json=await latte(seeded, "Oat milk"))
    placed = await client.post("/api/orders", json={"fulfilment": "pickup"})
    assert placed.status_code == 201
    order = placed.json()
    assert order["total_sar"] == "19.00" and order["status"] == "placed"
    assert order["restaurant"]["slug"] == CAFE
    assert order["lines"][0]["option_names"] == ["Small", "Oat milk"]
    listed = (await client.get("/api/orders")).json()
    assert [o["id"] for o in listed] == [order["id"]]
    assert (await client.get(f"/api/orders/{order['id']}")).json()["lines"] == order["lines"]
    assert (await client.get("/api/cart")).json()["lines"] == []


async def test_empty_cart_and_bad_fulfilment(client: httpx2.AsyncClient) -> None:
    await login(client, "ord_api_b")
    empty = await client.post("/api/orders", json={"fulfilment": "pickup"})
    assert empty.status_code == 409 and empty.json()["detail"]["code"] == "empty_cart"
    assert (await client.post("/api/orders", json={"fulfilment": "drone"})).status_code == 422


async def test_another_guests_order_is_not_found(
    seeded: AsyncSession, client: httpx2.AsyncClient, other_client: httpx2.AsyncClient
) -> None:
    await login(client, "ord_api_c")
    await login(other_client, "ord_api_d")
    await client.post("/api/cart/lines", json=await latte(seeded, "Soy milk"))
    order_id = (await client.post("/api/orders", json={"fulfilment": "dine_in"})).json()["id"]
    assert (await other_client.get(f"/api/orders/{order_id}")).status_code == 404
    assert (await other_client.get("/api/orders")).json() == []
    assert (await client.get("/api/orders")).status_code == 200


async def test_checkout_consent_names_the_reasons(
    seeded: AsyncSession, client: httpx2.AsyncClient
) -> None:
    await login(client, "ord_api_e")
    await client.post("/api/cart/lines", json=await latte(seeded, "Whole milk"))
    await allergic_to_dairy(seeded, "ord_api_e")  # said in the chat after adding it
    refused = await client.post("/api/orders", json={"fulfilment": "pickup"})
    assert refused.status_code == 409 and refused.json()["detail"]["reasons"] == ["dairy"]
    placed = await client.post(
        "/api/orders", json={"fulfilment": "pickup", "accepted_reasons": ["dairy"]}
    )
    assert placed.status_code == 201


async def test_an_order_for_a_total_the_guest_did_not_see_is_refused(
    seeded: AsyncSession, client: httpx2.AsyncClient
) -> None:
    await login(client, "ord_api_e")
    await client.post("/api/cart/lines", json=await latte(seeded, "Oat milk"))
    body = {"fulfilment": "pickup", "expected_total_sar": "16.00"}
    stale = await client.post("/api/orders", json=body)
    assert stale.status_code == 409 and stale.json()["detail"]["code"] == "cart_changed"
    body["expected_total_sar"] = "19.00"
    assert (await client.post("/api/orders", json=body)).status_code == 201
