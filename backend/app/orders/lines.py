"""Resolve cart lines against today's menu: price, allergens, names and conflicts.

Nothing about a line's price or safety is stored; it is worked out here on
every read and again at checkout.
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.configure import Configuration, ConfigurationError, configure
from app.menu.constraints import HardConstraints
from app.menu.queries import get_items_by_ids
from app.menu.schemas import MenuItemOut
from app.orders.models import Cart, CartLine
from app.orders.schemas import CartLineOut, LineOption


@dataclass(frozen=True)
class Resolved:
    line: CartLine
    item: MenuItemOut | None
    config: Configuration | None
    problem: str | None


async def resolve(session: AsyncSession, cart: Cart) -> list[Resolved]:
    rows = await get_items_by_ids(session, cart.restaurant_id, [ln.item_id for ln in cart.lines])
    items = {row.id: MenuItemOut.model_validate(row) for row in rows}
    resolved: list[Resolved] = []
    for line in cart.lines:
        item = items.get(line.item_id)
        if item is None:  # not expected: lines are deleted with their dish (FK cascade)
            resolved.append(Resolved(line, None, None, "This dish is no longer on the menu."))
            continue
        try:
            config = configure(item, line.option_ids, line.removed)
        except ConfigurationError as exc:
            resolved.append(Resolved(line, item, None, f"The menu changed: {exc}"))
            continue
        resolved.append(Resolved(line, item, config, None))
    return resolved


def line_out(r: Resolved, constraints: HardConstraints) -> CartLineOut:
    offered = {o.id: o for g in (r.item.option_groups if r.item else []) for o in g.options}
    options = [
        LineOption(id=i, name=offered[i].name, price_delta_sar=offered[i].price_delta_sar)
        for i in r.line.option_ids
        if i in offered
    ]
    unit = r.config.unit_price_sar if r.config else None
    return CartLineOut(
        id=r.line.id,
        item_id=r.line.item_id,
        name=r.item.name if r.item else "Unavailable dish",
        quantity=r.line.quantity,
        options=options,
        removed=r.line.removed,
        unit_price_sar=unit,
        line_total_sar=unit * r.line.quantity if unit is not None else None,
        allergens=r.config.allergens if r.config else [],
        conflicts_with_guest=constraints.violations(r.config) if r.config else [],
        may_contain_warnings=constraints.may_contain_warnings(r.config) if r.config else [],
        problem=r.problem,
    )


def total(lines: list[CartLineOut]) -> Decimal:
    return sum((ln.line_total_sar for ln in lines if ln.line_total_sar is not None), Decimal(0))
