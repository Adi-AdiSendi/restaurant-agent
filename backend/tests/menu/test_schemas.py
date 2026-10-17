"""MenuFilter limits become the search_menu tool's argument limits in phase 2."""

from typing import Any

import pytest
from pydantic import ValidationError

from app.menu.schemas import MenuFilter


@pytest.mark.parametrize(
    "bad",
    [
        {"max_spice": 4},
        {"max_spice": -1},
        {"max_price_sar": "0"},
        {"text": "x" * 101},
        {"exclude_allergens": ["lactose"]},
        {"category": "mains"},
    ],
)
def test_out_of_range_filter_is_rejected(bad: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        MenuFilter.model_validate(bad)


def test_empty_filter_is_valid() -> None:
    assert MenuFilter().exclude_allergens == []
