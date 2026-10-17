import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.pins import hash_pin, verify_pin
from app.users.service import (
    Credentials,
    InvalidCredentialsError,
    get_username,
    login_or_register,
)


async def test_pin_hash_verifies_only_the_right_pin() -> None:
    hashed = await hash_pin("1234")
    assert hashed != "1234"
    assert await verify_pin(hashed, "1234")
    assert not await verify_pin(hashed, "4321")
    assert not await verify_pin("garbage", "1234")


async def test_new_username_registers(session: AsyncSession) -> None:
    result = await login_or_register(session, Credentials(username="sara", pin="1234"))
    assert result.is_new
    assert await get_username(session, result.user_id) == "sara"


async def test_returning_user_logs_in_case_insensitively(session: AsyncSession) -> None:
    first = await login_or_register(session, Credentials(username="Omar", pin="1111"))
    again = await login_or_register(session, Credentials(username="  OMAR ", pin="1111"))
    assert not again.is_new
    assert again.user_id == first.user_id
    assert again.username == "omar"


async def test_wrong_pin_is_rejected(session: AsyncSession) -> None:
    await login_or_register(session, Credentials(username="lina", pin="1111"))
    with pytest.raises(InvalidCredentialsError):
        await login_or_register(session, Credentials(username="lina", pin="2222"))


@pytest.mark.parametrize(
    ("username", "pin"),
    [("ab", "1234"), ("has space", "1234"), ("x" * 21, "1234"), ("sara", "123"), ("sara", "12a4")],
)
def test_bad_credentials_shape_is_rejected(username: str, pin: str) -> None:
    with pytest.raises(ValidationError):
        Credentials(username=username, pin=pin)
