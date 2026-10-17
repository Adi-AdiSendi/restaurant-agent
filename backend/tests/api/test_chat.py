import httpx2
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_client import LLMUnavailableError, ModelTurn
from app.agent.tool_rounds import MAX_TOOL_ROUNDS
from app.config import get_settings
from app.memory.models import Message
from app.menu.queries import search_items
from app.menu.schemas import MenuFilter
from tests.agent.fake_llm import EMPTY_SEARCH, FakeLLM, answer_turn, extraction, op, tool_turn
from tests.api.conftest import active, login, new_conversation


async def chat(http: httpx2.AsyncClient, conversation_id: int, text: str) -> httpx2.Response:
    return await http.post("/api/chat", json={"conversation_id": conversation_id, "message": text})


async def test_chat_returns_reply_and_db_cards(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "sara")
    conversation = await new_conversation(client)
    sorbet = (await search_items(seeded, MenuFilter(text="sorbet")))[0]
    search = tool_turn("search_menu", EMPTY_SEARCH | {"text": "sorbet"})
    llm.turns.extend([search, answer_turn("Try the sorbet", [sorbet.id])])
    response = await chat(client, conversation, "Something sweet")
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Try the sorbet"
    assert body["items"][0]["name"] == "Mango Sorbet"
    assert body["items"][0]["price_sar"] == "22.00"


async def test_invalid_answer_is_502(llm: FakeLLM, client: httpx2.AsyncClient) -> None:
    await login(client, "sara")
    conversation = await new_conversation(client)
    llm.turns.extend([ModelTurn(output_text="nope"), ModelTurn(output_text="nope")])
    assert (await chat(client, conversation, "hi")).status_code == 502


async def test_endless_tool_calls_are_502(llm: FakeLLM, client: httpx2.AsyncClient) -> None:
    await login(client, "sara")
    conversation = await new_conversation(client)
    llm.turns.extend(tool_turn("search_menu", EMPTY_SEARCH) for _ in range(MAX_TOOL_ROUNDS + 1))
    assert (await chat(client, conversation, "hi")).status_code == 502


async def test_provider_down_is_503(llm: FakeLLM, client: httpx2.AsyncClient) -> None:
    await login(client, "sara")
    conversation = await new_conversation(client)
    llm.error = LLMUnavailableError("RateLimitError")
    response = await chat(client, conversation, "hi")
    assert response.status_code == 503
    assert response.json() == {"detail": "The assistant is unavailable."}


async def test_unknown_conversation_is_404(client: httpx2.AsyncClient) -> None:
    await login(client, "sara")
    assert (await chat(client, 999_999, "hi")).status_code == 404


async def test_bad_body_is_422(client: httpx2.AsyncClient) -> None:
    await login(client, "sara")
    conversation = await new_conversation(client)
    assert (await chat(client, conversation, "")).status_code == 422
    assert (await chat(client, conversation, "x" * 2001)).status_code == 422


async def test_slow_turn_is_504_and_saves_nothing(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "turn_deadline_seconds", 0.05)
    await login(client, "sara")
    conversation = await new_conversation(client)
    llm.extractions.append(extraction(op("add", "allergy", "egg")))
    llm.respond_delay = 5.0
    llm.turns.append(answer_turn("too late", []))
    response = await chat(client, conversation, "hi")
    assert response.status_code == 504
    assert response.json() == {"detail": "The assistant took too long. Please try again."}
    count = await seeded.scalar(select(func.count()).where(Message.conversation_id == conversation))
    assert count == 0
    assert await active(client) == []
