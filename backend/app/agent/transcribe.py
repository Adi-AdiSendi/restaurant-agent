"""Speech to text for voice input, when the browser cannot do it itself (English only).

The audio goes to OpenAI's transcription API; the key never leaves the server.
"""

from collections.abc import Awaitable, Callable

import openai
from openai import AsyncOpenAI

from app.config import get_settings

Transcriber = Callable[[bytes, str], Awaitable[str]]


class TranscribeError(Exception):
    """The voice service is not configured or did not answer."""


def _filename(mime_type: str) -> str:
    """OpenAI picks the decoder from the file name, so it must match the audio."""
    for kind, ext in (("mp4", "m4a"), ("ogg", "ogg"), ("wav", "wav"), ("mpeg", "mp3")):
        if kind in mime_type:
            return f"speech.{ext}"
    return "speech.webm"


async def openai_transcribe(audio: bytes, mime_type: str) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        raise TranscribeError("Voice input is not configured.")
    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=15.0, max_retries=1)
    try:
        result = await client.audio.transcriptions.create(
            model=settings.openai_transcribe_model,
            file=(_filename(mime_type), audio, mime_type),
            language="en",
        )
    except openai.OpenAIError as exc:
        raise TranscribeError("The voice service did not answer.") from exc
    return result.text.strip()
