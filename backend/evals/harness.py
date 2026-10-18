"""Run one case against the real agent path, inside a transaction that is rolled back.

Same entry point as POST /api/chat (`handle_message`), minus HTTP. Nothing a
case writes survives it, so the local DB stays clean. The menu must already be
seeded (the runner does it once): upserting it inside every case made
concurrent cases wait on each other's row locks.
"""

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.chat_turn import ConversationNotFoundError, handle_message
from app.agent.errors import AgentAnswerError, AgentLoopError, TurnTimeoutError
from app.agent.llm_client import AgentLLM, LLMUnavailableError
from app.db.engine import get_engine
from app.memory.conversations import start_conversation
from app.memory.profile import preference_history
from app.menu.constraints import NO_CONSTRAINTS
from app.orders.cart import get_cart
from app.orders.orders import list_orders
from app.users.models import User
from evals.case_model import Case, Step
from evals.transcript import CaseRun, StoredFact, Turn


async def run_case(case: Case, slot: int, run: int, llm: AgentLLM, deadline: float) -> CaseRun:
    """`slot` and `run` make usernames unique, so concurrent cases never collide."""
    async with get_engine().connect() as connection:
        outer = await connection.begin()
        session = AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        try:
            users = {name: await _user(session, f"ev{slot}_{run}_{name}") for name in case.users}
            # Each commit only releases a savepoint; the outer transaction still rolls
            # back. Committing setup keeps it when a failed turn rolls back its own work.
            await session.commit()
            conversations: dict[str, int] = {}
            turns = [
                await _turn(llm, session, case.restaurant, step, users, conversations, deadline)
                for step in case.steps
            ]
            profiles = {
                name: [
                    StoredFact(kind=p.kind, value=p.value, status=p.status)
                    for p in await preference_history(session, user_id)
                ]
                for name, user_id in users.items()
            }
        finally:
            await session.close()
            await outer.rollback()
    return CaseRun(case_id=case.id, category=case.category, run=run, turns=turns, profiles=profiles)


async def _user(session: AsyncSession, username: str) -> int:
    user = User(username=username, pin_hash="eval-user-never-logs-in")
    session.add(user)
    await session.flush()
    return user.id


async def _turn(
    llm: AgentLLM,
    session: AsyncSession,
    restaurant: str,
    step: Step,
    users: dict[str, int],
    conversations: dict[str, int],
    deadline: float,
) -> Turn:
    user_id = users[step.user]
    if step.new_conversation or step.restaurant or step.user not in conversations:
        restaurant = step.restaurant or restaurant
        conversation_id = await start_conversation(session, user_id, restaurant)
        assert conversation_id is not None, f"seed the menu first; no restaurant {restaurant}"
        conversations[step.user] = conversation_id
        await session.commit()
    target = conversations[step.into_conversation_of or step.user]
    started = time.perf_counter()
    result: dict[str, object] = {"user": step.user, "say": step.say}
    try:
        reply = await handle_message(llm, session, user_id, target, step.say, deadline)
        actions, menus = [a.kind for a in reply.actions], [m.category for m in reply.menus]
        result |= {"status": "ok", "reply": reply.reply, "cards": reply.items}
        result |= {"actions": actions, "menus": menus}
    except ConversationNotFoundError:
        result |= {"status": "refused"}
    except TurnTimeoutError:
        result |= {"status": "timeout"}
    except (LLMUnavailableError, AgentAnswerError, AgentLoopError) as exc:
        result |= {"status": "error", "error": type(exc).__name__}
    result["seconds"] = round(time.perf_counter() - started, 2)
    # Constraints only mark conflicts; the graders check names and quantities.
    result["cart"] = await get_cart(session, user_id, NO_CONSTRAINTS)
    result["orders"] = len(await list_orders(session, user_id))
    return Turn.model_validate(result)
