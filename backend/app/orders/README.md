# orders

Carts, checkout and orders (ADR 0019). Every function takes the session
user's ID; nothing here trusts a price or user from the client or the model.

- `models.py`: `Cart` (one per user, at one restaurant), `CartLine` (item,
  quantity, option IDs, removals), `Order` and `OrderLine` (a snapshot of
  names, prices, options, removals and allergens at checkout).
- `schemas.py`: `NewLine` (a dish as configured; it has no price field),
  `CartOut`, `CartLineOut`, `OrderSummary`, `OrderOut`.
- `lines.py`: resolves each cart line against today's menu through
  `menu/configure.py` (price, allergens, option names, conflicts). A line whose
  options changed gets a `problem`; a dish removed from the menu drops out.
- `cart.py` (`get_cart`), `cart_add.py` (`add_line`), `cart_edit.py`
  (`set_quantity`, `remove_line`, `clear_cart`). Writes lock the cart row.
  A choice that breaks the guest's allergies or diet raises `LineConflict`
  unless acknowledged; adding at another restaurant raises `OtherRestaurant`
  unless `replace_cart`. Identical choices merge, up to 20.
- `checkout.py`: `place_order`. Locks the cart; refuses an empty cart,
  unavailable lines and unacknowledged conflicts (checked again, since the
  profile may have changed); snapshots the lines and empties the cart.
- `orders.py`: `list_orders` (newest first), `get_order`. `status.py`:
  placed, preparing or ready, from the time since placing.
- `errors.py`: domain errors, each with a `code` the API returns.

Depends on: `menu`, `users`, `db`. Used by: `api`, and the phase 12 cart tools.
