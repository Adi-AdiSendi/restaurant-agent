"""Hard constraints through the HTTP API: a stored or just-stated allergy blocks
unsafe cards, whatever the fake model recommends."""

import httpx2
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.queries import search_items
from app.menu.schemas import MenuFilter
from tests.agent.fake_llm import FakeLLM, answer_turn, extraction, op, tool_turn
from tests.api.conftest import active, login, new_conversation, say


async def test_stored_allergy_blocks_an_unsafe_card_in_a_later_conversation(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "sara")
    first = await new_conversation(client)
    llm.extractions.append(extraction(op("add", "allergy", "peanut")))
    llm.turns.append(answer_turn("Noted.", []))
    await say(client, first, "I am allergic to peanuts")

    second = await new_conversation(client)
    thai = (await search_items(seeded, MenuFilter(text="peanut sauce")))[0].id
    get_thai = tool_turn("get_item", {"item_id": thai})
    llm.turns.extend([get_thai, answer_turn("Thai bowl!", [thai]), answer_turn("Thai!", [thai])])
    response = await client.post("/api/chat", json={"conversation_id": second, "message": "Hungry"})
    assert response.json()["items"] == []


async def test_allergy_stated_in_the_same_message_is_enforced_at_once(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    """Constraints are built after this message's memory operations are applied."""
    await login(client, "sara")
    conversation = await new_conversation(client)
    thai = (await search_items(seeded, MenuFilter(text="peanut sauce")))[0].id
    llm.extractions.append(extraction(op("add", "allergy", "peanut")))
    get_thai = tool_turn("get_item", {"item_id": thai})
    llm.turns.extend([get_thai, answer_turn("Thai bowl!", [thai]), answer_turn("Thai!", [thai])])
    message = "I am allergic to peanuts, can I get the Thai bowl?"
    response = await client.post(
        "/api/chat", json={"conversation_id": conversation, "message": message}
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert await active(client) == [("allergy", "peanut")]
