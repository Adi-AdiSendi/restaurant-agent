from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.conversations import add_message
from app.memory.models import Conversation
from app.memory.preference import Preference
from app.users.models import User
from app.users.service import Credentials, login_or_register
from scripts.seed_demo_users import seed_demo_users


async def user_id(session: AsyncSession, username: str) -> int:
    found = await session.scalar(select(User.id).where(User.username == username))
    assert found is not None
    return found


async def facts(session: AsyncSession, username: str) -> set[tuple[str, str, str]]:
    stmt = select(Preference).where(Preference.user_id == await user_id(session, username))
    return {(p.kind, p.value, p.status) for p in await session.scalars(stmt)}


async def test_alice_has_hard_facts_and_a_replaced_spice(session: AsyncSession) -> None:
    await seed_demo_users(session)
    assert await facts(session, "demo_alice") == {
        ("allergy", "peanut", "active"),
        ("diet", "vegetarian", "active"),
        ("spice", "hot", "superseded"),
        ("spice", "mild", "active"),
    }
    assert await facts(session, "demo_bob") == set()


async def test_demo_pins_log_in(session: AsyncSession) -> None:
    await seed_demo_users(session)
    for username, pin in (("demo_alice", "1234"), ("demo_bob", "5678")):
        result = await login_or_register(session, Credentials(username=username, pin=pin))
        assert not result.is_new


async def test_reseed_resets_what_a_reviewer_changed(session: AsyncSession) -> None:
    await seed_demo_users(session)
    bob = await user_id(session, "demo_bob")
    chat = Conversation(user_id=bob)
    session.add(chat)
    await session.flush()
    await add_message(session, chat.id, "user", "I am vegan now")
    session.add(Preference(user_id=bob, kind="diet", value="vegan"))
    await session.flush()

    await seed_demo_users(session)
    session.expire_all()
    assert await facts(session, "demo_bob") == set()
    new_bob = await user_id(session, "demo_bob")
    chats = await session.scalars(select(Conversation).where(Conversation.user_id == new_bob))
    assert list(chats) == []
