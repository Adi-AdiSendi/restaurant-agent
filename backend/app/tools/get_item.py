"""get_item: fetch one menu item by ID, with any conflict with the guest's constraints."""

from pydantic import BaseModel, Field, ValidationError

from app.menu.allergens import Allergen
from app.menu.queries import get_item
from app.menu.schemas import MenuItemOut
from app.tools.context import ToolContext
from app.tools.errors import ToolError, invalid_arguments
from app.tools.menu_views import ToolItem, tool_item

NAME = "get_item"

DESCRIPTION = """Fetch one menu item of this restaurant by its ID, with price, spice level, \
diet flags, ingredients, allergens, may_contain list, removable ingredients and every \
option group (each option with its price change, allergens and diet flags).
Use it when the user asks about a specific item you already have an ID for.
Input: {"item_id": <integer>}. Example: {"item_id": 7}
Do NOT use it to browse or filter the menu; use search_menu for that.
conflicts_with_guest lists why the guest cannot order it in any way (their saved \
allergies or diet). You may describe such an item, with a clear warning, but never \
recommend it. Each option's conflicts_with_guest says which choices they must avoid.
An unknown ID, or one from another restaurant, returns an error with error_category \
"not_found"."""

PARAMETERS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["item_id"],
    "properties": {"item_id": {"type": "integer"}},
}


class GetItemArgs(BaseModel):
    item_id: int = Field(ge=1)


class GetItemResult(BaseModel):
    item: ToolItem
    conflicts_with_guest: list[str]
    may_contain_warnings: list[Allergen]


async def handle(arguments: str, context: ToolContext) -> GetItemResult | ToolError:
    try:
        args = GetItemArgs.model_validate_json(arguments)
    except ValidationError as exc:
        return invalid_arguments(exc)
    row = await get_item(context.session, context.restaurant_id, args.item_id)
    if row is None:
        return ToolError(
            error_category="not_found",
            retryable=False,
            message=f"This restaurant has no menu item with id {args.item_id}.",
        )
    item = MenuItemOut.model_validate(row)
    constraints = context.constraints
    return GetItemResult(
        item=tool_item(item, constraints),
        conflicts_with_guest=constraints.item_violations(item),
        may_contain_warnings=constraints.item_may_contain_warnings(item),
    )
