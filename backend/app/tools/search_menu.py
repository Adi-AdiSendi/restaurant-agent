"""search_menu: filter this restaurant's menu in SQL and return full item records."""

from pydantic import BaseModel, ValidationError

from app.menu.allergens import Allergen
from app.menu.constraints import NO_CONSTRAINTS, HardConstraints
from app.menu.queries import search_items
from app.menu.schemas import MenuFilter, MenuItemOut
from app.tools.context import ToolContext
from app.tools.errors import ToolError, invalid_arguments
from app.tools.menu_views import ToolItem, tool_item

NAME = "search_menu"

DESCRIPTION = """Search this restaurant's menu. Returns every matching item with its ID, \
price, spice level, diet flags, ingredients, allergens, may_contain list, removable \
ingredients and option groups (each option with its price change, allergens, diet \
flags and conflicts_with_guest).
Use it before recommending anything, and again whenever the user's needs change.
Inputs: all fields are required; send null (or false / [] ) for anything not needed.
- category: one of this restaurant's categories (listed in your instructions), or null.
- vegan, vegetarian, exclude_allergens, max_price_sar, max_spice: use these for those \
needs. Do not put words like "vegan" or "pasta" in text. Prices are base prices; \
options can add to them.
- text: one dish or ingredient word, e.g. "salmon" or "pistachio".
Example: {"category": null, "max_price_sar": 45, "max_spice": 1, "vegetarian": false, \
"vegan": true, "exclude_allergens": ["peanut"], "text": null}
Do NOT use it to look up one item by ID; use get_item for that.
The guest's saved allergies and diet are always applied by the server (shown in \
guest_constraints_applied); you cannot turn them off. An item is only returned if \
some choice of its options suits the guest.
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
        "category": _nullable({"type": "string", "maxLength": 40}),
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
    items: list[ToolItem]
    guest_constraints_applied: HardConstraints = NO_CONSTRAINTS


async def handle(arguments: str, context: ToolContext) -> SearchMenuResult | ToolError:
    """The context's constraints come from the stored profile; arguments can only narrow."""
    try:
        model_filter = MenuFilter.model_validate_json(arguments)
    except ValidationError as exc:
        return invalid_arguments(exc)
    if model_filter.category is not None and model_filter.category not in context.categories:
        return ToolError(
            error_category="invalid_arguments",
            retryable=False,
            message=f"Unknown category {model_filter.category!r}. "
            f"Use one of: {', '.join(context.categories)}, or null.",
        )
    constraints = context.constraints
    rows = await search_items(
        context.session, context.restaurant_id, constraints.restrict(model_filter)
    )
    items = [MenuItemOut.model_validate(row) for row in rows]
    return SearchMenuResult(
        items=[tool_item(i, constraints) for i in items if not constraints.item_violations(i)],
        guest_constraints_applied=constraints,
    )
