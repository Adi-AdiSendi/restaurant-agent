"""The SDK adapter, tested against a fake AsyncOpenAI. No network."""

from types import SimpleNamespace
from typing import Any, cast

import httpx2
import openai
import pytest
from openai import AsyncOpenAI
from openai.types.responses import ResponseFunctionToolCall, ResponseReasoningItem
from pydantic_settings import SettingsConfigDict

from app.agent.answer import TEXT_FORMAT
from app.agent.llm_client import LLMUnavailableError, ModelTurn, ToolCall
from app.agent.openai_client import OpenAIResponsesClient, openai_client_from_settings
from app.config import Settings

REQUEST = httpx2.Request("POST", "https://api.openai.com/v1/responses")


class FakeResponses:
    def __init__(self, result: object = None, error: Exception | None = None) -> None:
        self.result, self.error = result, error
        self.kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> object:
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.result


def adapter(responses: FakeResponses) -> OpenAIResponsesClient:
    fake = cast(AsyncOpenAI, SimpleNamespace(responses=responses))
    return OpenAIResponsesClient(fake, "test-model")


async def respond(client: OpenAIResponsesClient) -> ModelTurn:
    return await client.respond(
        instructions="be helpful", input_items=[], tools=[], text_format=TEXT_FORMAT
    )


async def test_maps_calls_text_and_replay_items() -> None:
    reasoning = ResponseReasoningItem(
        id="rs_1", type="reasoning", summary=[], encrypted_content="enc"
    )
    call = ResponseFunctionToolCall(
        type="function_call", call_id="c1", name="get_item", arguments="{}"
    )
    message = SimpleNamespace(type="message")
    responses = FakeResponses(SimpleNamespace(output=[reasoning, message, call], output_text="hi"))
    turn = await respond(adapter(responses))
    assert turn.output_text == "hi"
    assert turn.tool_calls == [ToolCall("c1", "get_item", "{}")]
    assert [item["type"] for item in turn.replay_items] == ["reasoning", "function_call"]
    assert turn.replay_items[0]["encrypted_content"] == "enc"


async def test_sends_model_store_false_format_and_reasoning_include() -> None:
    responses = FakeResponses(SimpleNamespace(output=[], output_text="{}"))
    await respond(adapter(responses))
    assert responses.kwargs["model"] == "test-model"
    assert responses.kwargs["store"] is False
    assert responses.kwargs["text"] == {"format": TEXT_FORMAT}
    assert responses.kwargs["include"] == ["reasoning.encrypted_content"]


def status(code: int) -> httpx2.Response:
    return httpx2.Response(code, request=REQUEST)


@pytest.mark.parametrize(
    "error",
    [
        openai.APIConnectionError(request=REQUEST),
        openai.APITimeoutError(request=REQUEST),
        openai.AuthenticationError("bad key", response=status(401), body=None),
        openai.RateLimitError("slow down", response=status(429), body=None),
        openai.InternalServerError("oops", response=status(500), body=None),
        openai.NotFoundError("no such model", response=status(404), body=None),
    ],
)
async def test_provider_errors_become_unavailable(error: Exception) -> None:
    with pytest.raises(LLMUnavailableError):
        await respond(adapter(FakeResponses(error=error)))


class NoEnvFileSettings(Settings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")


def test_missing_api_key_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMUnavailableError):
        openai_client_from_settings(NoEnvFileSettings())


def test_client_uses_configured_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "model-from-env")
    client = openai_client_from_settings(NoEnvFileSettings())
    assert client._model == "model-from-env"  # pyright: ignore[reportPrivateUsage]
