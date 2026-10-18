"""A menu block in the chat, end to end through POST /api/chat with a scripted model."""

import httpx2

from tests.agent.fake_llm import FakeLLM, answer_turn, extraction, op, tool_turn
from tests.api.conftest import login, new_conversation


async def test_a_shown_category_comes_back_as_a_menu_block_with_conflicts_marked(
    llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "menu_block")
    conversation = await new_conversation(client, "bean-and-bloom")
    llm.extractions.append(extraction(op("add", "allergy", "dairy")))
    llm.turns.extend(
        [tool_turn("show_menu", {"category": "coffee"}), answer_turn("Here is our coffee.", [])]
    )
    body = (
        await client.post(
            "/api/chat", json={"conversation_id": conversation, "message": "Dairy allergy. Coffee?"}
        )
    ).json()
    [block] = body["menus"]
    assert block["category"] == "coffee" and body["items"] == []
    latte = next(item for item in block["items"] if item["name"] == "Latte")
    whole = next(
        o for g in latte["option_groups"] for o in g["options"] if o["name"] == "Whole milk"
    )
    assert whole["conflicts_with_guest"] == ["dairy"]
