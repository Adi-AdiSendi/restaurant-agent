"""Voice to text over HTTP, with a fake transcriber (tests never call OpenAI)."""

import httpx2
import pytest

from app.agent.transcribe import TranscribeError
from app.api import transcribe as route
from tests.api.conftest import login


async def post_audio(client: httpx2.AsyncClient, audio: bytes = b"RIFF....WAVE") -> httpx2.Response:
    headers = {"content-type": "audio/wav"}
    return await client.post("/api/transcribe", content=audio, headers=headers)


@pytest.fixture
def heard(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every mime type the fake was called with; it answers with a fixed sentence."""
    calls: list[str] = []

    async def fake(audio: bytes, mime_type: str) -> str:
        calls.append(mime_type)
        return "a small latte with oat milk"

    monkeypatch.setattr(route, "openai_transcribe", fake)
    route.RECENT.clear()
    return calls


async def test_a_guest_gets_the_text_of_their_recording(
    client: httpx2.AsyncClient, heard: list[str]
) -> None:
    await login(client, "voice_a")
    response = await post_audio(client)
    assert response.status_code == 200
    assert response.json() == {"text": "a small latte with oat milk"}
    assert heard == ["audio/wav"]


async def test_login_is_required(client: httpx2.AsyncClient, heard: list[str]) -> None:
    assert (await post_audio(client)).status_code == 401
    assert heard == []


async def test_empty_and_oversized_audio_are_refused(
    client: httpx2.AsyncClient, heard: list[str]
) -> None:
    await login(client, "voice_b")
    assert (await post_audio(client, b"")).status_code == 400
    assert (await post_audio(client, b"0" * (route.MAX_AUDIO_BYTES + 1))).status_code == 413
    assert heard == []


async def test_a_guest_is_rate_limited(client: httpx2.AsyncClient, heard: list[str]) -> None:
    await login(client, "voice_c")
    for _ in range(route.RATE_LIMIT):
        assert (await post_audio(client)).status_code == 200
    assert (await post_audio(client)).status_code == 429


async def test_a_failed_voice_service_is_503(
    client: httpx2.AsyncClient, heard: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def broken(audio: bytes, mime_type: str) -> str:
        raise TranscribeError("The voice service did not answer.")

    monkeypatch.setattr(route, "openai_transcribe", broken)
    await login(client, "voice_d")
    assert (await post_audio(client)).status_code == 503
