"""Log in a returning user or register a new one."""

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, StringConstraints
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User
from app.users.pins import hash_pin, verify_pin


def _normalize(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


# Normalize before the pattern check, so "  Omar " is the same user as "omar".
Username = Annotated[
    str, BeforeValidator(_normalize), StringConstraints(pattern=r"^[a-z0-9_]{3,20}$")
]
Pin = Annotated[str, StringConstraints(pattern=r"^[0-9]{4}$")]


class Credentials(BaseModel):
    username: Username
    pin: Pin


class LoginResult(BaseModel):
    user_id: int
    username: str
    is_new: bool


class InvalidCredentialsError(Exception):
    """Known username with the wrong PIN."""


class UsernameTakenError(Exception):
    """Another request registered the same new username at the same moment."""


async def login_or_register(session: AsyncSession, credentials: Credentials) -> LoginResult:
    user = await session.scalar(select(User).where(User.username == credentials.username))
    if user is None:
        user = User(username=credentials.username, pin_hash=await hash_pin(credentials.pin))
        session.add(user)
        try:
            await session.flush()
        except IntegrityError as exc:
            await session.rollback()
            raise UsernameTakenError from exc
        return LoginResult(user_id=user.id, username=user.username, is_new=True)
    if not await verify_pin(user.pin_hash, credentials.pin):
        raise InvalidCredentialsError
    return LoginResult(user_id=user.id, username=user.username, is_new=False)


async def get_username(session: AsyncSession, user_id: int) -> str | None:
    return await session.scalar(select(User.username).where(User.id == user_id))


async def lock_user(session: AsyncSession, user_id: int) -> None:
    """Row lock until the transaction ends, so one user's chat turns run one at a time."""
    await session.execute(select(User.id).where(User.id == user_id).with_for_update())
