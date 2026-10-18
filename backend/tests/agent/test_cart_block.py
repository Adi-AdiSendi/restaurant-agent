from decimal import Decimal

from app.agent.cart_block import cart_block
from app.orders.schemas import CartOut
from tests.agent.test_turn_reply import CART, LATTE

EMPTY = CartOut(restaurant=None, lines=[], total_sar=Decimal(0), item_count=0)


def test_the_cart_block_names_each_line_id() -> None:
    block = cart_block(CART, "bean-and-bloom")
    assert "line_id 7: 2 x Latte (Oat milk, no sugar), 38.00 SAR" in block
    assert "another restaurant" not in block


def test_a_cart_elsewhere_says_it_must_be_emptied_first() -> None:
    assert "Ask the guest before using clear_cart" in cart_block(CART, "stack-and-smash")


def test_an_empty_cart_is_one_line() -> None:
    assert cart_block(EMPTY, "bean-and-bloom") == "The guest's cart is empty."


def test_a_line_that_breaks_the_profile_says_so() -> None:
    line = LATTE.model_copy(update={"conflicts_with_guest": ["dairy"]})
    cart = CART.model_copy(update={"lines": [line]})
    assert "Not suitable for the guest: dairy" in cart_block(cart, "bean-and-bloom")
