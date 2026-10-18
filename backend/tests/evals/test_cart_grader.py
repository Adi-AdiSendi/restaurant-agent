from decimal import Decimal

from app.orders.schemas import CartLineOut, CartOut, LineOption
from evals.expectations import Expect, LineExpect
from evals.graders.cards import grade_turn
from evals.graders.cart import grade_cart
from evals.report import p95
from evals.transcript import Turn


def line(
    name: str, quantity: int = 1, options: tuple[str, ...] = (), removed: tuple[str, ...] = ()
) -> CartLineOut:
    return CartLineOut(
        id=1,
        item_id=1,
        name=name,
        quantity=quantity,
        options=[
            LineOption(id=n, name=o, price_delta_sar=Decimal(0)) for n, o in enumerate(options)
        ],
        removed=list(removed),
        unit_price_sar=Decimal(1),
        line_total_sar=Decimal(quantity),
        allergens=[],
        conflicts_with_guest=[],
        may_contain_warnings=[],
        problem=None,
    )


def turn(*lines: CartLineOut, orders: int = 0, actions: tuple[str, ...] = ()) -> Turn:
    cart = CartOut(restaurant=None, lines=list(lines), total_sar=Decimal(0), item_count=0)
    return Turn(
        user="u", say="x", status="ok", seconds=1, cart=cart, orders=orders, actions=list(actions)
    )


LATTE = LineExpect(name="Latte", options=["Small", "Oat milk"])


def test_the_cart_must_hold_exactly_the_expected_lines() -> None:
    expect = Expect(cart=[LATTE])
    [ok] = grade_cart(expect, turn(line("Latte", options=("Oat milk", "Small"))), "turn 1")
    assert ok.passed
    [wrong_milk] = grade_cart(expect, turn(line("Latte", options=("Small", "Whole milk"))), "t")
    assert not wrong_milk.passed and "missing ['Latte']" in wrong_milk.detail
    extra = turn(line("Latte", options=("Small", "Oat milk")), line("Fries"))
    assert not grade_cart(expect, extra, "t")[0].passed


def test_quantity_and_removals_count_and_unset_fields_are_free() -> None:
    expect = Expect(cart=[LineExpect(name="Classic Smash", quantity=2, removed=["pickles"])])
    good = turn(line("Classic Smash", 2, options=("Single patty",), removed=("pickles",)))
    assert grade_cart(expect, good, "t")[0].passed
    assert not grade_cart(expect, turn(line("Classic Smash", 2)), "t")[0].passed
    one = turn(line("Classic Smash", 1, removed=("pickles",)))
    assert not grade_cart(expect, one, "t")[0].passed


def test_an_empty_cart_orders_and_the_checkout_card() -> None:
    expect = Expect(cart=[], orders=0, checkout_card=True)
    checks = grade_cart(expect, turn(actions=("checkout",)), "t")
    assert [c.passed for c in checks] == [True, True, True]
    checks = grade_cart(expect, turn(line("Latte"), orders=1), "t")
    assert [c.passed for c in checks] == [False, False, False]


def test_p95_is_the_slowest_turn_but_one_in_twenty() -> None:
    assert p95([]) == 0.0
    assert p95([3.0]) == 3.0
    assert p95([float(n) for n in range(1, 21)]) == 19.0


def menu_passed(expect: Expect, *menus: str) -> bool:
    turn = Turn(user="u", say="x", status="ok", seconds=1, menus=list(menus))
    return next(c for c in grade_turn(expect, turn, "t") if "menu" in c.name).passed


def test_the_menu_block_must_be_exactly_the_asked_category() -> None:
    expect = Expect(menu="desserts")
    assert menu_passed(expect, "desserts")
    assert not menu_passed(expect)
    assert not menu_passed(expect, "desserts", "drinks")
