"""What a chat turn returns: the answer, the cart after the turn, and action cards.

Action cards come only from tool results, never from model text (ADR 0019), so
the guest sees what the server actually changed.
"""

from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel

from app.agent.schemas import AgentReply, Card
from app.orders.cart import get_cart
from app.orders.schemas import CartLineOut, CartOut
from app.tools.cart_results import CartChange, CheckoutProposal
from app.tools.context import ToolContext
from app.tools.show_menu import ShowMenuResult


class Action(BaseModel):
    kind: Literal["added", "updated", "removed", "cleared", "checkout"]
    quantity: int
    line: CartLineOut | None
    left_out: list[str]
    """Ingredients left out because the guest dislikes them."""


class MenuBlock(BaseModel):
    """A category the guest asked to see. Not a recommendation: unsuitable dishes are
    marked by the server (conflicts_with_guest) and cannot be added from it."""

    category: str
    items: list[Card]


class ChatReply(AgentReply):
    """POST /api/chat: the answer, what the turn changed, and the cart as it is now."""

    actions: list[Action]
    cart: CartOut
    menus: list[MenuBlock]


def menus_from(results: Iterable[BaseModel]) -> list[MenuBlock]:
    """One block per category shown this turn, in order; items come from the tool result."""
    blocks: dict[str, MenuBlock] = {}
    for r in results:
        if isinstance(r, ShowMenuResult):
            items = [Card(**item.model_dump()) for item in r.items]
            blocks[r.category] = MenuBlock(category=r.category, items=items)
    return list(blocks.values())


def actions_from(results: Iterable[BaseModel]) -> list[Action]:
    """One card per successful change, in order, and at most one checkout card, last."""
    actions: list[Action] = []
    checkout = False
    for result in results:
        if isinstance(result, CartChange):
            left_out = result.left_out_for_dislikes
            actions.append(
                Action(
                    kind=result.action,
                    quantity=result.quantity,
                    line=result.line,
                    left_out=left_out,
                )
            )
        elif isinstance(result, CheckoutProposal):
            checkout = True
    if checkout:
        actions.append(Action(kind="checkout", quantity=0, line=None, left_out=[]))
    return actions


async def finish(context: ToolContext, reply: AgentReply, results: list[BaseModel]) -> ChatReply:
    cart = await get_cart(context.session, context.user_id, context.constraints)
    return ChatReply(
        reply=reply.reply,
        items=reply.items,
        actions=actions_from(results),
        cart=cart,
        menus=menus_from(results),
    )
