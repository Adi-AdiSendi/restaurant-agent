import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.errors import AgentAnswerError, AgentLoopError
from app.agent.llm_client import InputItem, ModelTurn
from app.agent.loop import run_turn
from app.agent.prompt import SYSTEM_PROMPT as PROMPT
from app.agent.tool_rounds import MAX_TOOL_ROUNDS, RETRY_TOOL_ROUNDS
from app.menu.constraints import NO_CONSTRAINTS as NONE
from app.menu.schemas import MenuFilter
from tests.agent.fake_llm import EMPTY_SEARCH, FakeLLM, answer_turn, tool_turn
from tests.contexts import corner_items, tool_context

ASK: list[InputItem] = [{"role": "user", "content": "Something vegan and mild, please"}]
VEGAN_SEARCH = tool_turn("search_menu", EMPTY_SEARCH | {"vegan": True})


async def id_of(session: AsyncSession, name: str) -> int:
    items = await corner_items(session, MenuFilter(text=name))
    return next(i.id for i in items if i.name == name)


async def test_tool_call_then_answer_returns_db_cards(seeded: AsyncSession) -> None:
    bowl = await id_of(seeded, "Mediterranean Veggie Bowl")
    llm = FakeLLM([VEGAN_SEARCH, answer_turn("Try it", [bowl])])
    result = await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    assert result.reply == "Try it"
    assert [item.name for item in result.items] == ["Mediterranean Veggie Bowl"]
    assert str(result.items[0].price_sar) == "39.00"


async def test_full_tool_output_goes_back_to_the_model(seeded: AsyncSession) -> None:
    llm = FakeLLM([VEGAN_SEARCH, answer_turn("ok", [])])
    await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    call, output = llm.calls[1][-2], llm.calls[1][-1]
    assert call["type"] == "function_call"
    assert output["type"] == "function_call_output"
    assert output["call_id"] == call["call_id"]
    items = json.loads(str(output["output"]))["items"]
    assert len(items) == len(await corner_items(seeded, MenuFilter(vegan=True)))
    assert {"allergens", "may_contain", "price_sar", "spice_level"} <= set(items[0])


async def test_reasoning_items_are_replayed_before_tool_output(seeded: AsyncSession) -> None:
    reasoning: InputItem = {
        "type": "reasoning",
        "id": "rs_1",
        "summary": [],
        "encrypted_content": "x",
    }
    search = tool_turn("search_menu", EMPTY_SEARCH, reasoning=reasoning)
    llm = FakeLLM([search, answer_turn("ok", [])])
    await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    assert [item.get("type") for item in llm.calls[1][-3:]] == [
        "reasoning",
        "function_call",
        "function_call_output",
    ]


async def test_unknown_item_ids_are_dropped(seeded: AsyncSession) -> None:
    bowl = await id_of(seeded, "Mediterranean Veggie Bowl")
    llm = FakeLLM([VEGAN_SEARCH, answer_turn("Here", [999_999, bowl])])
    result = await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    assert [item.id for item in result.items] == [bowl]


async def test_ids_no_tool_returned_are_dropped(seeded: AsyncSession) -> None:
    """The vegan search never returned the salmon, so it cannot become a card."""
    salmon = await id_of(seeded, "Grilled Salmon Plate")
    bowl = await id_of(seeded, "Mediterranean Veggie Bowl")
    llm = FakeLLM([VEGAN_SEARCH, answer_turn("Here", [salmon, bowl])])
    result = await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    assert [item.id for item in result.items] == [bowl]


async def test_answer_without_any_tool_call_has_no_cards(seeded: AsyncSession) -> None:
    bowl = await id_of(seeded, "Mediterranean Veggie Bowl")
    llm = FakeLLM([answer_turn("Guessing", [bowl])])
    result = await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    assert result.items == []


async def test_invalid_answer_is_retried_once_with_the_error(seeded: AsyncSession) -> None:
    llm = FakeLLM([ModelTurn(output_text='{"reply": ""}'), answer_turn("Fixed", [])])
    result = await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    assert result.reply == "Fixed"
    retry_note = llm.calls[1][-1]
    assert retry_note["role"] == "developer"
    assert "recommended_item_ids" in str(retry_note["content"])
    assert "reply" in str(retry_note["content"])


async def test_two_invalid_answers_raise(seeded: AsyncSession) -> None:
    llm = FakeLLM([ModelTurn(output_text="not json"), ModelTurn(output_text="still not")])
    with pytest.raises(AgentAnswerError):
        await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)


async def test_endless_tool_calls_fail_loudly(seeded: AsyncSession) -> None:
    turns = [tool_turn("search_menu", EMPTY_SEARCH) for _ in range(MAX_TOOL_ROUNDS + 1)]
    llm = FakeLLM(turns)
    with pytest.raises(AgentLoopError):
        await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    assert len(llm.calls) == MAX_TOOL_ROUNDS + 1


async def test_retry_gets_a_smaller_tool_budget(seeded: AsyncSession) -> None:
    retry_tools = [tool_turn("search_menu", EMPTY_SEARCH) for _ in range(RETRY_TOOL_ROUNDS + 1)]
    llm = FakeLLM([ModelTurn(output_text="bad"), *retry_tools])
    with pytest.raises(AgentLoopError):
        await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    assert len(llm.calls) == 1 + RETRY_TOOL_ROUNDS + 1


async def test_unknown_tool_returns_error_to_model(seeded: AsyncSession) -> None:
    llm = FakeLLM([tool_turn("place_order", {}), answer_turn("Sorry", [])])
    await run_turn(llm, await tool_context(seeded, NONE), ASK, instructions=PROMPT)
    output = json.loads(str(llm.calls[1][-1]["output"]))
    assert output["error_category"] == "unknown_tool"
    assert output["retryable"] is False


async def test_input_items_are_sent_in_order(seeded: AsyncSession) -> None:
    history: list[InputItem] = [
        {"role": "developer", "content": "Guest profile: nothing saved yet."},
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello! Hungry?"},
        {"role": "user", "content": "Very"},
    ]
    llm = FakeLLM([answer_turn("Great", [])])
    await run_turn(llm, await tool_context(seeded, NONE), history, instructions=PROMPT)
    assert llm.calls[0] == history


async def test_ids_shown_earlier_in_the_conversation_are_allowed(seeded: AsyncSession) -> None:
    bowl = await id_of(seeded, "Mediterranean Veggie Bowl")
    llm = FakeLLM([answer_turn("Good choice, the bowl", [bowl])])
    result = await run_turn(
        llm, await tool_context(seeded, NONE), ASK, seen_ids={bowl}, instructions=PROMPT
    )
    assert [item.id for item in result.items] == [bowl]
