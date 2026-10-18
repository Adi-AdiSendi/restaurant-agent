"""Everything the model gets for one turn, built by the server from the session.

The profile block, the history, the cart at the start of the turn, the tool
context (user, restaurant, constraints, dislikes) and the system prompt.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.cart_block import cart_block
from app.agent.context import build_input
from app.agent.llm_client import InputItem
from app.agent.prompt import system_prompt
from app.memory.models import Message
from app.memory.preference import Preference
from app.memory.profile import dislikes, hard_constraints
from app.menu.queries import list_restaurants
from app.menu.restaurant import Restaurant
from app.orders.cart import get_cart
from app.tools.context import ToolContext


@dataclass
class TurnSetup:
    context: ToolContext
    items: list[InputItem]
    seen_ids: set[int]
    instructions: str


async def prepare_turn(
    session: AsyncSession,
    user_id: int,
    conversation_id: int,
    restaurant: Restaurant,
    profile: Sequence[Preference],
    history: list[Message],
    update_note: str | None,
) -> TurnSetup:
    constraints = hard_constraints(profile)
    context = ToolContext(
        session,
        user_id,
        conversation_id,
        restaurant.id,
        restaurant.slug,
        tuple(restaurant.categories),
        constraints,
        dislikes(profile),
    )
    items, seen = build_input(profile, history, update_note)
    cart = await get_cart(session, user_id, constraints)
    # Right after the profile block, so it reads as standing context, not history.
    items.insert(1, {"role": "developer", "content": cart_block(cart, restaurant.slug)})
    others = [r for r in await list_restaurants(session) if r.id != restaurant.id]
    return TurnSetup(context, items, seen, system_prompt(restaurant, others))
