"""In-loop ASGI client sharing the test's rolled-back DB session and a FakeLLM."""

from collections.abc import AsyncIterator

import httpx2
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.chat import get_llm_client
from app.db.engine import get_session
from app.main import create_app
from tests.agent.fake_llm import FakeLLM


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM([])


async def _client(session: AsyncSession, llm: FakeLLM) -> AsyncIterator[httpx2.AsyncClient]:
    async def test_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_session] = test_session
    app.dependency_overrides[get_llm_client] = lambda: llm
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture
async def client(seeded: AsyncSession, llm: FakeLLM) -> AsyncIterator[httpx2.AsyncClient]:
    async for http in _client(seeded, llm):
        yield http


@pytest.fixture
async def other_client(seeded: AsyncSession, llm: FakeLLM) -> AsyncIterator[httpx2.AsyncClient]:
    """A second browser: same app and DB, its own cookie jar."""
    async for http in _client(seeded, llm):
        yield http


async def login(http: httpx2.AsyncClient, username: str, pin: str = "1234") -> None:
    response = await http.post("/api/auth/login", json={"username": username, "pin": pin})
    assert response.status_code == 200, response.text


async def new_conversation(http: httpx2.AsyncClient, restaurant: str | None = None) -> int:
    body = {"restaurant": restaurant} if restaurant else None
    response = await http.post("/api/conversations", json=body)
    assert response.status_code == 201
    return int(response.json()["id"])


async def say(http: httpx2.AsyncClient, conversation_id: int, text: str) -> None:
    response = await http.post(
        "/api/chat", json={"conversation_id": conversation_id, "message": text}
    )
    assert response.status_code == 200, response.text


async def active(http: httpx2.AsyncClient) -> list[tuple[str, str]]:
    rows = (await http.get("/api/preferences")).json()
    return [(r["kind"], r["value"]) for r in rows if r["status"] == "active"]
