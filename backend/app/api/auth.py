"""Log in or register, log out, and the current user."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id
from app.db.engine import get_session
from app.users.service import (
    Credentials,
    InvalidCredentialsError,
    UsernameTakenError,
    get_username,
    login_or_register,
)

router = APIRouter(prefix="/auth")


class LoginResponse(BaseModel):
    username: str
    is_new: bool


class Me(BaseModel):
    username: str


@router.post("/login")
async def login(
    body: Credentials, request: Request, session: AsyncSession = Depends(get_session)
) -> LoginResponse:
    try:
        result = await login_or_register(session, body)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail="Wrong PIN for this username.") from exc
    except UsernameTakenError as exc:
        raise HTTPException(status_code=409, detail="That username was just taken.") from exc
    await session.commit()
    request.session.clear()
    request.session["user_id"] = result.user_id
    return LoginResponse(username=result.username, is_new=result.is_new)


@router.post("/logout", status_code=204)
async def logout(request: Request) -> None:
    request.session.clear()


@router.get("/me")
async def me(
    user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> Me:
    return Me(username=await get_username(session, user_id) or "")
