"""The hand-written strict tool schemas must not drift from the Pydantic models."""

from typing import cast

import pytest

from app.agent.tool_dispatch import TOOL_SPECS
from app.menu.schemas import MenuFilter
from app.tools import (
    add_to_cart,
    get_item,
    propose_checkout,
    recent_orders,
    remove_cart_line,
    search_menu,
    show_menu,
    update_cart_line,
    view_cart,
)
from app.tools.add_to_cart import AddToCartArgs
from app.tools.cart_results import NoArguments
from app.tools.get_item import GetItemArgs
from app.tools.remove_cart_line import RemoveCartLineArgs
from app.tools.show_menu import ShowMenuArgs
from app.tools.update_cart_line import UpdateCartLineArgs


@pytest.mark.parametrize(
    ("parameters", "fields"),
    [
        (search_menu.PARAMETERS, set(MenuFilter.model_fields)),
        (get_item.PARAMETERS, set(GetItemArgs.model_fields)),
        (add_to_cart.PARAMETERS, set(AddToCartArgs.model_fields)),
        (update_cart_line.PARAMETERS, set(UpdateCartLineArgs.model_fields)),
        (remove_cart_line.PARAMETERS, set(RemoveCartLineArgs.model_fields)),
        (view_cart.PARAMETERS, set(NoArguments.model_fields)),
        (recent_orders.PARAMETERS, set(NoArguments.model_fields)),
        (propose_checkout.PARAMETERS, set(NoArguments.model_fields)),
        (show_menu.PARAMETERS, set(ShowMenuArgs.model_fields)),
    ],
)
def test_schema_lists_every_field_as_required(
    parameters: dict[str, object], fields: set[str]
) -> None:
    properties = cast(dict[str, object], parameters["properties"])
    required = cast(list[str], parameters["required"])
    assert set(properties) == set(required) == fields
    assert parameters["additionalProperties"] is False


def test_no_tool_can_place_an_order() -> None:
    """ADR 0019: only the guest's checkout button places an order."""
    names = {cast(str, spec["name"]) for spec in TOOL_SPECS}
    assert len(names) == 9 and not any("place" in name for name in names)
