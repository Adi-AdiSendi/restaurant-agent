from decimal import Decimal

from app.agent.cart_block import cart_block
from app.agent.turn_reply import actions_from
from app.orders.schemas import CartLineOut, CartOut, CartRestaurant, LineOption
from app.tools.cart_results import CartChange, CheckoutProposal, RecentOrders
from app.tools.errors import ToolError

LATTE = CartLineOut(
    id=7,
    item_id=40,
    name="Latte",
    quantity=2,
    options=[LineOption(id=2, name="Oat milk", price_delta_sar=Decimal("3.00"))],
    removed=["sugar"],
    unit_price_sar=Decimal("19.00"),
    line_total_sar=Decimal("38.00"),
    allergens=[],
    conflicts_with_guest=[],
    may_contain_warnings=[],
    problem=None,
)
CAFE = CartRestaurant(slug="bean-and-bloom", name="Bean & Bloom")
CART = CartOut(restaurant=CAFE, lines=[LATTE], total_sar=Decimal("38.00"), item_count=2)
EMPTY = CartOut(restaurant=None, lines=[], total_sar=Decimal(0), item_count=0)


def test_the_cart_block_names_each_line_id() -> None:
    block = cart_block(CART, "bean-and-bloom")
    assert "line_id 7: 2 x Latte (Oat milk, no sugar), 38.00 SAR" in block
    assert "another restaurant" not in block


def test_a_cart_elsewhere_says_it_must_be_emptied_first() -> None:
    assert '"Empty cart"' in cart_block(CART, "stack-and-smash")


def test_an_empty_cart_is_one_line() -> None:
    assert cart_block(EMPTY, "bean-and-bloom") == "The guest's cart is empty."


def test_actions_come_only_from_successful_changes() -> None:
    added = CartChange(action="added", quantity=1, line=LATTE, cart=CART)
    refused = ToolError(error_category="conflict", retryable=False, message="dairy")
    proposal = CheckoutProposal(cart=CART, note="")
    results = [added, refused, proposal, RecentOrders(orders=[]), proposal]
    assert [(a.kind, a.quantity) for a in actions_from(results)] == [
        ("added", 1),
        ("checkout", 0),
    ]
