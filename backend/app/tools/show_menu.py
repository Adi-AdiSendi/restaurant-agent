"""show_menu: one category of this restaurant's menu, shown to the guest as a menu block."""

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.menu.guest_view import GuestItem, guest_item
from app.menu.queries import search_items
from app.menu.restaurant import CATEGORY_PATTERN
from app.menu.schemas import MenuFilter, MenuItemOut
from app.tools.context import ToolContext
from app.tools.errors import ToolError, invalid_arguments

NAME = "show_menu"

DESCRIPTION = """Show the guest one category of this restaurant's menu as a menu block \
under your reply: every dish in it, with price, photo and options. Dishes that break \
the guest's allergies or diet are shown greyed, with the reason, and cannot be added \
from the block.
Use it when the guest asks to see the menu or a part of it ("what desserts do you \
have?", "show me the drinks").
Input: {"category": <one of this restaurant's categories>}. Example: {"category": "desserts"}
Do NOT use it to recommend: showing a dish is not recommending it. To recommend, \
use search_menu and put IDs in recommended_item_ids. Keep your reply short; the block \
lists the dishes, so do not repeat them."""

PARAMETERS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["category"],
    "properties": {"category": {"type": "string", "maxLength": 40}},
}


class ShowMenuArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(pattern=CATEGORY_PATTERN, max_length=40)


class ShowMenuResult(BaseModel):
    category: str
    items: list[GuestItem]
    """Every dish in the category; conflicts_with_guest says which do not suit the guest."""


async def handle(arguments: str, context: ToolContext) -> ShowMenuResult | ToolError:
    try:
        args = ShowMenuArgs.model_validate_json(arguments)
    except ValidationError as exc:
        return invalid_arguments(exc)
    if args.category not in context.categories:
        return ToolError(
            error_category="invalid_arguments",
            retryable=False,
            message=f"Unknown category {args.category!r}. "
            f"Use one of: {', '.join(context.categories)}.",
        )
    rows = await search_items(
        context.session, context.restaurant_id, MenuFilter(category=args.category)
    )
    items = [guest_item(MenuItemOut.model_validate(r), context.constraints) for r in rows]
    return ShowMenuResult(category=args.category, items=items)
