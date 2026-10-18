"""Restaurants are listed, and a conversation belongs to the one it was started at."""

import httpx2
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.menu_sync import sync_restaurant
from tests.agent.fake_llm import EMPTY_SEARCH, FakeLLM, answer_turn, tool_turn
from tests.api.conftest import login, new_conversation
from tests.contexts import corner_items
from tests.factories import TEST_CAFE


async def test_restaurants_are_listed_in_order_without_login(client: httpx2.AsyncClient) -> None:
    response = await client.get("/api/restaurants")
    assert response.status_code == 200
    first = response.json()[0]
    assert first["slug"] == "corner-table"
    expected = {"id", "slug", "name", "cuisine", "tagline", "accent_color", "categories", "photo"}
    assert set(first) == expected


async def test_unknown_restaurant_is_404(client: httpx2.AsyncClient) -> None:
    await login(client, "sara")
    response = await client.post("/api/conversations", json={"restaurant": "nowhere"})
    assert response.status_code == 404


async def test_a_chat_at_another_restaurant_never_shows_corner_table_dishes(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await sync_restaurant(seeded, TEST_CAFE, 9)
    await login(client, "sara")
    conversation = await new_conversation(client, "test-cafe")
    corner_dish = (await corner_items(seeded))[0].id
    llm.turns.extend(
        [tool_turn("search_menu", EMPTY_SEARCH), answer_turn("Try these", [corner_dish])]
    )
    response = await client.post(
        "/api/chat", json={"conversation_id": conversation, "message": "Something warm"}
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert "for Test Cafe, a cafe restaurant" in llm.instructions[0]
    search_output = llm.calls[1][-1]
    assert "Latte" in str(search_output) and "Truffle" not in str(search_output)
