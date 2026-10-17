"""The post-check, end to end through run_turn with a fake model that tries to
recommend unsafe items. No path may return a card that breaks a constraint."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_client import InputItem, ModelTurn, ToolCall
from app.agent.loop import NO_SAFE_MATCH, SAFE_MATCHES, run_turn
from app.menu.allergens import Allergen
from app.menu.constraints import HardConstraints
from app.menu.schemas import MenuFilter, MenuItemOut
from tests.agent.fake_llm import FakeLLM, answer_turn
from tests.contexts import corner_items, tool_context

ASK: list[InputItem] = [{"role": "user", "content": "What should I order?"}]
PROMPT = "You are a test assistant."
PEANUT = HardConstraints(excluded_allergens=frozenset({Allergen.PEANUT}))


def fetch(*item_ids: int) -> ModelTurn:
    """One model turn that calls get_item for each ID (so they count as seen)."""
    calls = [ToolCall(f"c{i}", "get_item", json.dumps({"item_id": i})) for i in item_ids]
    replay: list[InputItem] = [
        {"type": "function_call", "call_id": c.call_id, "name": c.name, "arguments": c.arguments}
        for c in calls
    ]
    return ModelTurn(output_text="", tool_calls=calls, replay_items=replay)


async def menu(session: AsyncSession) -> list[MenuItemOut]:
    return [MenuItemOut.model_validate(r) for r in await corner_items(session, MenuFilter())]


async def id_of(session: AsyncSession, text: str) -> int:
    return (await corner_items(session, MenuFilter(text=text)))[0].id


CASES = [HardConstraints(excluded_allergens=frozenset({a})) for a in Allergen] + [
    HardConstraints(vegetarian=True),
    HardConstraints(vegan=True, vegetarian=True),
]


@pytest.mark.parametrize("constraints", CASES)
async def test_a_model_recommending_everything_never_gets_a_violating_card(
    seeded: AsyncSession, constraints: HardConstraints
) -> None:
    items = await menu(seeded)
    for start in range(0, len(items), 5):
        chunk = [i.id for i in items[start : start + 5]]
        llm = FakeLLM(
            [fetch(*chunk), answer_turn("All of these!", chunk), answer_turn("Still", chunk)]
        )
        result = await run_turn(
            llm, await tool_context(seeded, constraints), ASK, instructions=PROMPT
        )
        expected = {i.id for i in items if i.id in chunk and not constraints.violations(i)}
        assert {card.id for card in result.items} == expected
        assert all(not constraints.violations(card) for card in result.items)


async def test_blocked_card_gets_one_corrective_retry(seeded: AsyncSession) -> None:
    thai, bowl = await id_of(seeded, "peanut sauce"), await id_of(seeded, "veggie bowl")
    llm = FakeLLM(
        [fetch(thai, bowl), answer_turn("Thai bowl!", [thai]), answer_turn("Bowl", [bowl])]
    )
    result = await run_turn(llm, await tool_context(seeded, PEANUT), ASK, instructions=PROMPT)
    assert result.reply == "Bowl"
    assert [card.id for card in result.items] == [bowl]
    note = llm.calls[-1][-1]
    assert note["role"] == "developer"
    assert "Thai Peanut Noodle Bowl" in str(note["content"])
    assert "peanut" in str(note["content"])


async def test_still_unsafe_after_retry_gives_the_fixed_safe_reply(seeded: AsyncSession) -> None:
    thai = await id_of(seeded, "peanut sauce")
    llm = FakeLLM([fetch(thai), answer_turn("Thai!", [thai]), answer_turn("Thai again!", [thai])])
    result = await run_turn(llm, await tool_context(seeded, PEANUT), ASK, instructions=PROMPT)
    assert result.reply == NO_SAFE_MATCH
    assert result.items == []


async def test_partly_unsafe_after_retry_keeps_only_safe_cards(seeded: AsyncSession) -> None:
    thai, bowl = await id_of(seeded, "peanut sauce"), await id_of(seeded, "veggie bowl")
    both = [thai, bowl]
    llm = FakeLLM([fetch(*both), answer_turn("Both", both), answer_turn("Both again", both)])
    result = await run_turn(llm, await tool_context(seeded, PEANUT), ASK, instructions=PROMPT)
    assert result.reply == SAFE_MATCHES
    assert [card.id for card in result.items] == [bowl]


async def test_item_from_earlier_now_unsafe_is_dropped(seeded: AsyncSession) -> None:
    """Recommended before the guest mentioned the allergy; must not come back."""
    thai = await id_of(seeded, "peanut sauce")
    llm = FakeLLM([answer_turn("The Thai bowl again?", [thai]), answer_turn("Thai", [thai])])
    result = await run_turn(
        llm, await tool_context(seeded, PEANUT), ASK, seen_ids={thai}, instructions=PROMPT
    )
    assert result.items == []


async def test_may_contain_item_is_a_card_with_a_warning(seeded: AsyncSession) -> None:
    cake = await id_of(seeded, "lava")
    nuts = HardConstraints(excluded_allergens=frozenset({Allergen.TREE_NUT}))
    llm = FakeLLM([fetch(cake), answer_turn("Lava cake, check with staff", [cake])])
    result = await run_turn(llm, await tool_context(seeded, nuts), ASK, instructions=PROMPT)
    assert [(c.name, c.may_contain_warnings) for c in result.items] == [
        ("Chocolate Lava Cake", [Allergen.TREE_NUT])
    ]


async def test_failed_safety_retry_falls_back_instead_of_erroring(seeded: AsyncSession) -> None:
    """The retry loops on tools: the turn still ends safely, not with a 502."""
    thai, bowl = await id_of(seeded, "peanut sauce"), await id_of(seeded, "veggie bowl")
    looping = [fetch(bowl), fetch(bowl)]
    llm = FakeLLM([fetch(thai, bowl), answer_turn("Both", [thai, bowl]), *looping])
    result = await run_turn(llm, await tool_context(seeded, PEANUT), ASK, instructions=PROMPT)
    assert result.reply == SAFE_MATCHES
    assert [card.id for card in result.items] == [bowl]


async def test_failed_safety_retry_with_nothing_safe_says_so(seeded: AsyncSession) -> None:
    thai = await id_of(seeded, "peanut sauce")
    bad = [ModelTurn(output_text="nope"), ModelTurn(output_text="nope")]
    llm = FakeLLM([fetch(thai), answer_turn("Thai", [thai]), *bad])
    result = await run_turn(llm, await tool_context(seeded, PEANUT), ASK, instructions=PROMPT)
    assert result.reply == NO_SAFE_MATCH
    assert result.items == []
