"""The post-check every recommended item passes before it reaches the user.

The rule itself is `HardConstraints.violations` (in `menu`, so `get_item` can
report the same conflicts). This module decides what reaches the user:
violating items are blocked, `may_contain` items pass with a warning.
"""

from collections.abc import Sequence

from pydantic import BaseModel

from app.menu.constraints import HardConstraints
from app.menu.schemas import MenuItemOut


class Blocked(BaseModel):
    item_id: int
    name: str
    reasons: list[str]


class GuardResult(BaseModel):
    allowed: list[MenuItemOut]
    blocked: list[Blocked]


def check(items: Sequence[MenuItemOut], constraints: HardConstraints) -> GuardResult:
    allowed: list[MenuItemOut] = []
    blocked: list[Blocked] = []
    for item in items:
        reasons = constraints.violations(item)
        if reasons:
            blocked.append(Blocked(item_id=item.id, name=item.name, reasons=reasons))
        else:
            allowed.append(item)
    return GuardResult(allowed=allowed, blocked=blocked)
