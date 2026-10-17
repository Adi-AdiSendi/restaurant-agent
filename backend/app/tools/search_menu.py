"""search_menu: filter the menu in SQL and return full item records."""

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.categories import Category
from app.menu.constraints import NO_CONSTRAINTS, HardConstraints
from app.menu.queries import search_items
from app.menu.schemas import MenuFilter, MenuItemOut
from app.tools.errors import ToolError, invalid_arguments

NAME = "search_menu"

DESCRIPTION = """Search the restaurant menu. Returns every matching item with its ID, \
price, spice level, diet flags, ingredients, allergens and may_contain list.
Use it before recommending anything, and again whenever the user's needs change.
Inputs: all fields are required; send null (or false / [] ) for anything not needed.
- category, vegan, vegetarian, exclude_allergens, max_price_sar, max_spice: use these \
for those needs. Do not put words like "vegan" or "pasta" in text.
- text: one dish or ingredient word, e.g. "salmon" or "pistachio".
Example: {"category": null, "max_price_sar": 45, "max_spice": 1, "vegetarian": false, \
"vegan": true, "exclude_allergens": ["peanut"], "text": null}
Do NOT use it to look up one item by ID; use get_item for that.
The guest's saved allergies and diet are always applied by the server (shown in \
guest_constraints_applied); you cannot turn them off.
No match returns {"items": []}, which is a valid answer, not an error."""


def _nullable(schema: dict[str, object]) -> dict[str, object]:
    return {"anyOf": [schema, {"type": "null"}]}


PARAMETERS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "category",
        "max_price_sar",
        "max_spice",
        "vegetarian",
        "vegan",
        "exclude_allergens",
        "text",
    ],
    "properties": {
        "category": _nullable({"type": "string", "enum": [c.value for c in Category]}),
        "max_price_sar": _nullable({"type": "number"}),
        "max_spice": _nullable({"type": "integer", "minimum": 0, "maximum": 3}),
        "vegetarian": {"type": "boolean"},
        "vegan": {"type": "boolean"},
        "exclude_allergens": {
            "type": "array",
            "items": {"type": "string", "enum": [a.value for a in Allergen]},
        },
        "text": _nullable({"type": "string", "maxLength": 100}),
    },
}


class SearchMenuResult(BaseModel):
    items: list[MenuItemOut]
    guest_constraints_applied: HardConstraints = NO_CONSTRAINTS


async def handle(
    session: AsyncSession, arguments: str, constraints: HardConstraints
) -> SearchMenuResult | ToolError:
    """`constraints` come from the stored profile; the model's arguments can only narrow."""
    try:
        model_filter = MenuFilter.model_validate_json(arguments)
    except ValidationError as exc:
        return invalid_arguments(exc)
    rows = await search_items(session, constraints.restrict(model_filter))
    return SearchMenuResult(
        items=[MenuItemOut.model_validate(row) for row in rows],
        guest_constraints_applied=constraints,
    )
