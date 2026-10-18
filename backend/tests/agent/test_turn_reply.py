from decimal import Decimal

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


def test_actions_come_only_from_successful_changes() -> None:
    added = CartChange(action="added", quantity=1, line=LATTE, cart=CART)
    refused = ToolError(error_category="conflict", retryable=False, message="dairy")
    proposal = CheckoutProposal(cart=CART, note="")
    results = [added, refused, proposal, RecentOrders(orders=[]), proposal]
    assert [(a.kind, a.quantity) for a in actions_from(results)] == [
        ("added", 1),
        ("checkout", 0),
    ]
