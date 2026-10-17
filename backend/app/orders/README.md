# orders

Carts, checkout and orders (ADR 0019). Every function takes the session
user's ID; nothing here trusts a price or user from the client or the model.

- `models.py`: `Cart` (one per user, at one restaurant), `CartLine` (item,
  quantity, option IDs, removals), `Order` and `OrderLine` (a snapshot of
  names, prices, options, removals and allergens at checkout).

Depends on: `menu`, `users`, `db`. Used by: `api`, and the phase 12 cart tools.
