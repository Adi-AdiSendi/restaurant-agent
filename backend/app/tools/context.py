"""What every tool handler gets from the server for one turn (ADR 0020).

Built from the session and the stored conversation, never from model
arguments: the model cannot reach another user's data or another
restaurant's menu by what it sends.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.constraints import HardConstraints


@dataclass(frozen=True)
class ToolContext:
    session: AsyncSession
    user_id: int
    conversation_id: int
    restaurant_id: int
    restaurant_slug: str
    categories: tuple[str, ...]
    """This restaurant's menu categories, in menu order."""
    constraints: HardConstraints
    dislikes: tuple[str, ...] = ()
    """The guest's active dislikes (soft), used to leave out removable ingredients."""
