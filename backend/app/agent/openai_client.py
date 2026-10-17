"""LLMClient backed by the OpenAI Responses API."""

import logging
from functools import lru_cache
from typing import Any, cast

import openai
from openai import AsyncOpenAI

from app.agent.llm_client import InputItem, LLMUnavailableError, ModelTurn, Spec, ToolCall
from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class OpenAIResponsesClient:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def respond(
        self,
        *,
        instructions: str,
        input_items: list[InputItem],
        tools: list[Spec],
        text_format: Spec,
    ) -> ModelTurn:
        try:
            # Any: our plain dicts match the SDK's TypedDict params at runtime;
            # the cast keeps the SDK's large param unions out of our interface.
            response = await self._client.responses.create(
                model=self._model,
                instructions=instructions,
                input=cast(Any, input_items),
                tools=cast(Any, tools),
                text=cast(Any, {"format": text_format}),
                include=["reasoning.encrypted_content"],
                store=False,
            )
        except openai.APIError as exc:
            raise _unavailable(exc) from exc
        calls = [
            ToolCall(call_id=item.call_id, name=item.name, arguments=item.arguments)
            for item in response.output
            if item.type == "function_call"
        ]
        replay = [
            item.model_dump(exclude_none=True)
            for item in response.output
            if item.type in ("reasoning", "function_call")
        ]
        return ModelTurn(output_text=response.output_text, tool_calls=calls, replay_items=replay)

    async def complete_json(
        self, *, instructions: str, user_input: str, text_format: dict[str, object]
    ) -> str:
        """One structured call with no tools, used for memory extraction."""
        try:
            response = await self._client.responses.create(
                model=self._model,
                instructions=instructions,
                input=user_input,
                text=cast(Any, {"format": text_format}),
                store=False,
            )
        except openai.APIError as exc:
            raise _unavailable(exc) from exc
        return response.output_text


def _unavailable(exc: openai.APIError) -> LLMUnavailableError:
    status = getattr(exc, "status_code", None)
    logger.error("llm_error type=%s status=%s", type(exc).__name__, status)
    return LLMUnavailableError(type(exc).__name__)


def openai_client_from_settings(settings: Settings) -> OpenAIResponsesClient:
    if not settings.openai_api_key:
        raise LLMUnavailableError("OPENAI_API_KEY is not set")
    sdk = AsyncOpenAI(api_key=settings.openai_api_key, timeout=15.0, max_retries=1)
    return OpenAIResponsesClient(sdk, settings.openai_model)


@lru_cache
def default_openai_client() -> OpenAIResponsesClient:
    return openai_client_from_settings(get_settings())
