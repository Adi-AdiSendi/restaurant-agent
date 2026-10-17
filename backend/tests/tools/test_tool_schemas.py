"""The hand-written strict tool schemas must not drift from the Pydantic models."""

from typing import cast

import pytest

from app.menu.schemas import MenuFilter
from app.tools import get_item, search_menu
from app.tools.get_item import GetItemArgs


@pytest.mark.parametrize(
    ("parameters", "fields"),
    [
        (search_menu.PARAMETERS, set(MenuFilter.model_fields)),
        (get_item.PARAMETERS, set(GetItemArgs.model_fields)),
    ],
)
def test_schema_lists_every_field_as_required(
    parameters: dict[str, object], fields: set[str]
) -> None:
    properties = cast(dict[str, object], parameters["properties"])
    required = cast(list[str], parameters["required"])
    assert set(properties) == set(required) == fields
    assert parameters["additionalProperties"] is False
