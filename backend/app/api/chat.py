"""POST /api/chat: one message in a conversation owned by the logged-in user."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.chat_turn import ConversationNotFoundError, handle_message
from app.agent.errors import AgentAnswerError, AgentLoopError, TurnTimeoutError
from app.agent.llm_client import AgentLLM, LLMUnavailableError
from app.agent.openai_client import default_openai_client
from app.agent.schemas import AgentReply
from app.api.deps import current_user_id
from app.config import Settings, get_settings
from app.db.engine import get_session

router = APIRouter()


class ChatRequest(BaseModel):
    conversation_id: int
    message: str = Field(min_length=1, max_length=2000)


def get_llm_client() -> AgentLLM:
    try:
        return default_openai_client()
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail="The assistant is not configured.") from exc


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user_id: int = Depends(current_user_id),
    llm: AgentLLM = Depends(get_llm_client),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AgentReply:
    try:
        return await handle_message(
            llm,
            session,
            user_id,
            body.conversation_id,
            body.message,
            settings.turn_deadline_seconds,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found.") from exc
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail="The assistant is unavailable.") from exc
    except TurnTimeoutError as exc:
        raise HTTPException(
            status_code=504, detail="The assistant took too long. Please try again."
        ) from exc
    except (AgentAnswerError, AgentLoopError) as exc:
        raise HTTPException(
            status_code=502, detail="The assistant gave an invalid answer."
        ) from exc
