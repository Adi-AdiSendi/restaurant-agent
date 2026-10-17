"""Phase 3 done-when, through the HTTP API with a fake LLM and real Postgres:
memory crosses conversations, corrections replace facts, users stay isolated."""

import httpx2
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_client import ModelTurn
from app.memory.models import Message
from app.menu.schemas import MenuFilter
from tests.agent.fake_llm import EMPTY_SEARCH, FakeLLM, answer_turn, extraction, op, tool_turn
from tests.api.conftest import active, login, new_conversation, say
from tests.contexts import corner_items


async def test_fact_from_conversation_one_reaches_conversation_two(
    llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "sara")
    first = await new_conversation(client)
    llm.extractions.append(extraction(op("add", "diet", "vegan")))
    llm.turns.append(answer_turn("Noted, vegan it is.", []))
    await say(client, first, "I'm vegan")

    second = await new_conversation(client)
    llm.turns.append(answer_turn("Here are vegan picks.", []))
    await say(client, second, "What should I get?")
    profile_item = llm.calls[-1][0]
    assert profile_item["role"] == "developer"
    assert "vegan" in str(profile_item["content"])
    assert all("I'm vegan" not in str(i.get("content")) for i in llm.calls[-1])


async def test_correction_replaces_the_old_fact(llm: FakeLLM, client: httpx2.AsyncClient) -> None:
    await login(client, "omar")
    conversation = await new_conversation(client)
    llm.extractions.append(extraction(op("add", "diet", "vegetarian")))
    llm.turns.append(answer_turn("Got it.", []))
    await say(client, conversation, "I'm vegetarian")
    [row] = [r for r in (await client.get("/api/preferences")).json() if r["kind"] == "diet"]

    llm.extractions.append(extraction(op("remove", "diet", "vegetarian", row["id"])))
    llm.turns.append(answer_turn("Fish is back on the menu.", []))
    await say(client, conversation, "Actually I eat fish now")
    assert await active(client) == []
    assert "vegetarian" not in str(llm.calls[-1][0]["content"])


async def test_users_are_isolated(
    llm: FakeLLM, client: httpx2.AsyncClient, other_client: httpx2.AsyncClient
) -> None:
    await login(client, "alice")
    alice_chat = await new_conversation(client)
    llm.extractions.append(extraction(op("add", "allergy", "peanut")))
    llm.turns.append(answer_turn("No peanuts, noted.", []))
    await say(client, alice_chat, "I'm allergic to peanuts")

    await login(other_client, "bob")
    assert await active(other_client) == []
    response = await other_client.post(
        "/api/chat", json={"conversation_id": alice_chat, "message": "what did alice say?"}
    )
    assert response.status_code == 404
    assert await active(client) == [("allergy", "peanut")]


async def test_failed_turn_saves_nothing(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "sara")
    conversation = await new_conversation(client)
    llm.extractions.append(extraction(op("add", "allergy", "egg")))
    llm.turns.extend([ModelTurn(output_text="bad"), ModelTurn(output_text="still bad")])
    response = await client.post(
        "/api/chat", json={"conversation_id": conversation, "message": "x"}
    )
    assert response.status_code == 502
    stmt = select(func.count()).where(Message.conversation_id == conversation)
    count = await seeded.scalar(stmt)
    assert count == 0
    assert await active(client) == []


async def test_item_from_earlier_in_the_conversation_can_be_a_card_again(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    """ "I'll take the bowl": no new search needed for an item already recommended."""
    await login(client, "sara")
    conversation = await new_conversation(client)
    bowl = (await corner_items(seeded, MenuFilter(text="veggie bowl")))[0].id
    llm.turns.extend([tool_turn("search_menu", EMPTY_SEARCH), answer_turn("Try the bowl", [bowl])])
    await say(client, conversation, "Something light")
    llm.turns.append(answer_turn("Great choice", [bowl]))
    response = await client.post(
        "/api/chat", json={"conversation_id": conversation, "message": "I'll take the bowl"}
    )
    assert [item["id"] for item in response.json()["items"]] == [bowl]
    assert any("Item IDs recommended above" in str(i.get("content")) for i in llm.calls[-1])


async def test_extraction_sees_the_previous_assistant_message(
    llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "sara")
    conversation = await new_conversation(client)
    llm.turns.append(answer_turn("Any allergies I should know about?", []))
    await say(client, conversation, "Hi")
    llm.turns.append(answer_turn("Noted.", []))
    await say(client, conversation, "peanuts")
    assert "Any allergies I should know about?" in llm.extraction_inputs[-1]
