"""Ordering through the chat, end to end through POST /api/chat with a scripted model."""

import json

import httpx2
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_client import InputItem, ModelTurn, Spec
from app.config import get_settings
from tests.agent.fake_llm import FakeLLM, answer_turn, extraction, op, tool_turn
from tests.api.conftest import login, new_conversation
from tests.tools.cart_tool_helpers import BURGERS, CAFE, latte_args, smash_args


async def chat(http: httpx2.AsyncClient, conversation_id: int, text: str) -> httpx2.Response:
    return await http.post("/api/chat", json={"conversation_id": conversation_id, "message": text})


def tool_output(call: list[InputItem]) -> dict[str, object]:
    output = next(i for i in reversed(call) if i.get("type") == "function_call_output")
    return json.loads(str(output["output"]))


async def test_an_add_returns_an_action_card_and_the_cart(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "order_add")
    conversation = await new_conversation(client, CAFE)
    llm.turns.extend(
        [tool_turn("add_to_cart", await latte_args(seeded)), answer_turn("Added a latte.", [])]
    )
    body = (await chat(client, conversation, "A small oat latte please")).json()
    [action] = body["actions"]
    assert action["kind"] == "added" and action["line"]["name"] == "Latte"
    assert body["cart"]["item_count"] == 1 and body["cart"]["total_sar"] == "19.00"
    assert (await client.get("/api/cart")).json()["item_count"] == 1

    # The next turn shows the model the cart with its line ids.
    llm.turns.append(answer_turn("You have a latte.", []))
    await chat(client, conversation, "What's in my cart?")
    line_id = body["cart"]["lines"][0]["id"]
    assert f"line_id {line_id}: 1 x Latte (Small, Oat milk)" in str(llm.calls[-1][1]["content"])


async def test_a_conflict_is_refused_and_nothing_is_added(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "order_dairy")
    conversation = await new_conversation(client, CAFE)
    llm.extractions.append(extraction(op("add", "allergy", "dairy")))
    whole = tool_turn("add_to_cart", await latte_args(seeded, "Whole milk"))
    llm.turns.extend([whole, answer_turn("Whole milk has dairy.", [])])
    body = (await chat(client, conversation, "Dairy allergy. Latte with whole milk")).json()
    assert body["actions"] == [] and body["cart"]["lines"] == []
    assert tool_output(llm.calls[1])["error_category"] == "conflict"


async def test_a_disliked_ingredient_is_left_out_and_reported(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "order_pickles")
    conversation = await new_conversation(client, BURGERS)
    llm.extractions.append(extraction(op("add", "dislike", "pickles")))
    llm.turns.extend(
        [tool_turn("add_to_cart", await smash_args(seeded)), answer_turn("Added, no pickles.", [])]
    )
    body = (await chat(client, conversation, "I hate pickles. A Classic Smash please")).json()
    [action] = body["actions"]
    assert action["left_out"] == ["pickles"] and action["line"]["removed"] == ["pickles"]


async def test_checkout_shows_a_card_and_places_nothing(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "order_checkout")
    conversation = await new_conversation(client, CAFE)
    llm.turns.extend(
        [
            tool_turn("add_to_cart", await latte_args(seeded)),
            tool_turn("propose_checkout", {}, call_id="call_2"),
            answer_turn("Use the button to place it.", []),
        ]
    )
    body = (await chat(client, conversation, "A latte, and place the order")).json()
    assert [a["kind"] for a in body["actions"]] == ["added", "checkout"]
    assert (await client.get("/api/orders")).json() == []


async def test_a_failed_turn_undoes_its_cart_changes(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "order_invalid")
    conversation = await new_conversation(client, CAFE)
    bad = ModelTurn(output_text="not json")
    llm.turns.extend([tool_turn("add_to_cart", await latte_args(seeded)), bad, bad])
    assert (await chat(client, conversation, "A latte")).status_code == 502
    assert (await client.get("/api/cart")).json()["lines"] == []


async def test_a_timed_out_turn_undoes_its_cart_changes(
    seeded: AsyncSession,
    llm: FakeLLM,
    client: httpx2.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "turn_deadline_seconds", 0.5)
    await login(client, "order_slow")
    conversation = await new_conversation(client, CAFE)
    llm.turns.extend(
        [tool_turn("add_to_cart", await latte_args(seeded)), answer_turn("too late", [])]
    )
    respond = llm.respond

    async def slow_after_the_add(
        *, instructions: str, input_items: list[InputItem], tools: list[Spec], text_format: Spec
    ) -> ModelTurn:
        llm.respond_delay = 5.0 if llm.calls else 0.0
        return await respond(
            instructions=instructions, input_items=input_items, tools=tools, text_format=text_format
        )

    monkeypatch.setattr(llm, "respond", slow_after_the_add)
    assert (await chat(client, conversation, "A latte")).status_code == 504
    assert (await client.get("/api/cart")).json()["lines"] == []
