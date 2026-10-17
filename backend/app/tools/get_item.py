"""get_item: fetch one menu item by ID, with any conflict with the guest's constraints."""

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.constraints import HardConstraints
from app.menu.queries import get_item
from app.menu.schemas import MenuItemOut
from app.tools.errors import ToolError, invalid_arguments

NAME = "get_item"

DESCRIPTION = """Fetch one menu item by its ID, with price, spice level, diet flags, \
ingredients, allergens and may_contain list.
Use it when the user asks about a specific item you already have an ID for.
Input: {"item_id": <integer>}. Example: {"item_id": 7}
Do NOT use it to browse or filter the menu; use search_menu for that.
conflicts_with_guest lists why the guest must not order it (their saved allergies \
or diet). You may describe such an item, with a clear warning, but never recommend it.
An unknown ID returns an error with error_category "not_found"."""

PARAMETERS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["item_id"],
    "properties": {"item_id": {"type": "integer"}},
}


class GetItemArgs(BaseModel):
    item_id: int = Field(ge=1)


class GetItemResult(BaseModel):
    item: MenuItemOut
    conflicts_with_guest: list[str]
    may_contain_warnings: list[Allergen]


async def handle(
    session: AsyncSession, arguments: str, constraints: HardConstraints
) -> GetItemResult | ToolError:
    try:
        args = GetItemArgs.model_validate_json(arguments)
    except ValidationError as exc:
        return invalid_arguments(exc)
    row = await get_item(session, args.item_id)
    if row is None:
        return ToolError(
            error_category="not_found",
            retryable=False,
            message=f"No menu item has id {args.item_id}.",
        )
    item = MenuItemOut.model_validate(row)
    return GetItemResult(
        item=item,
        conflicts_with_guest=constraints.violations(item),
        may_contain_warnings=constraints.may_contain_warnings(item),
    )
