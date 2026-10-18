"""POST /api/transcribe: the guest's recorded voice to text, for the message box."""

import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.agent.transcribe import TranscribeError, Transcriber, openai_transcribe
from app.api.deps import current_user_id

router = APIRouter()

MAX_AUDIO_BYTES = 10 * 1024 * 1024
RATE_LIMIT, RATE_WINDOW_S = 20, 300.0
"""Each call spends money, so a guest gets 20 clips per 5 minutes."""
RECENT: defaultdict[int, deque[float]] = defaultdict(deque)
"""Each guest's recent call times; in memory, so it resets when the server restarts."""


class Transcript(BaseModel):
    text: str


def get_transcriber() -> Transcriber:
    return openai_transcribe


def _check_rate(user_id: int) -> None:
    now, calls = time.monotonic(), RECENT[user_id]
    while calls and now - calls[0] > RATE_WINDOW_S:
        calls.popleft()
    if len(calls) >= RATE_LIMIT:
        raise HTTPException(429, "Too many voice messages. Please wait a minute.")
    calls.append(now)


@router.post("/transcribe")
async def transcribe(
    request: Request,
    user_id: int = Depends(current_user_id),
    transcriber: Transcriber = Depends(get_transcriber),
) -> Transcript:
    if int(request.headers.get("content-length") or 0) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "That recording is too long. Please keep it short.")
    audio = await request.body()
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "That recording is too long. Please keep it short.")
    if not audio:
        raise HTTPException(400, "No audio was received.")
    _check_rate(user_id)
    mime_type = request.headers.get("content-type") or "audio/webm"
    try:
        return Transcript(text=await transcriber(audio, mime_type))
    except TranscribeError as exc:
        raise HTTPException(503, str(exc)) from exc
