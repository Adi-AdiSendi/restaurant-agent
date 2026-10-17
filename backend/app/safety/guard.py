"""The post-check every recommended item passes before it reaches the user.

The rule itself is `HardConstraints.item_violations` (in `menu`, so the tools
report the same conflicts): the base must fit, and every required option group
must keep a fitting choice. This module decides what reaches the user:
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
        reasons = constraints.item_violations(item)
        if reasons:
            blocked.append(Blocked(item_id=item.id, name=item.name, reasons=reasons))
        else:
            allowed.append(item)
    return GuardResult(allowed=allowed, blocked=blocked)
