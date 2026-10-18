"""The guest edits their own preferences by hand: the Preferences page (ADR 0026).

Each route returns the whole history, as `GET /api/preferences` does, so the
page can redraw from one response.
"""

from collections.abc import Awaitable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id
from app.db.engine import get_session
from app.memory.manual_edit import (
    InvalidPreference,
    PreferenceNotFound,
    add_preference,
    change_preference,
    remove_preference,
)
from app.memory.profile import PreferenceOut
from app.memory.vocabulary import Kind

router = APIRouter()


class NewPreference(BaseModel):
    kind: Kind
    value: str = Field(min_length=1, max_length=60)


class ChangedValue(BaseModel):
    value: str = Field(min_length=1, max_length=60)


async def _saved(
    session: AsyncSession, change: Awaitable[list[PreferenceOut]]
) -> list[PreferenceOut]:
    try:
        history = await change
    except InvalidPreference as exc:
        detail = {"code": "invalid_preference", "message": str(exc)}
        raise HTTPException(status_code=422, detail=detail) from exc
    except PreferenceNotFound as exc:
        detail = {"code": "not_found", "message": "That preference is not saved any more."}
        raise HTTPException(status_code=404, detail=detail) from exc
    await session.commit()
    return history


@router.post("/preferences", status_code=201)
async def add(
    body: NewPreference,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> list[PreferenceOut]:
    return await _saved(session, add_preference(session, user_id, body.kind, body.value))


@router.patch("/preferences/{pref_id}")
async def change(
    pref_id: int,
    body: ChangedValue,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> list[PreferenceOut]:
    return await _saved(session, change_preference(session, user_id, pref_id, body.value))


@router.delete("/preferences/{pref_id}")
async def remove(
    pref_id: int,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> list[PreferenceOut]:
    return await _saved(session, remove_preference(session, user_id, pref_id))
