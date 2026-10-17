# 0019: Cart, orders, and a checkout only the guest confirms

- Status: Accepted
- Date: 2026-10-17

## Context
v2 lets guests order, both by hand from the menu and through the chat. The
model may change the cart, so we must decide what it is allowed to commit.

## Decision
- The cart lives on the server: one open cart per user, tied to one
  restaurant. Each line holds an item, a quantity, option IDs and removals.
  Switching restaurant with items in the cart asks before clearing it.
- Prices are always recomputed from the database. The client and the model
  never send a price.
- Placing an order snapshots names, options and prices into `orders` and
  `order_lines`, so later menu changes do not rewrite history.
- No payment. Checkout offers pickup or dine-in and says "Pay at the
  counter". The order status (placed, preparing, ready) is derived from the
  time since placement, so no background jobs are needed.
- The chat may add, change and remove cart lines. It can never place an
  order: it can only show a checkout card, and the order is placed by the
  guest's button. This follows the confirm-card pattern from the
  Aviation-Services concierge.
- An item that conflicts with the guest's allergy or diet:
  - through the chat: refused, and the model explains why;
  - by hand: refused until the guest acknowledges a clear warning. It is
    their choice to make, not the model's.
- The model still answers `{reply, recommended_item_ids}`. Cart changes are
  reported from tool results, never from model text.

## Alternatives considered
- A browser-only cart: simpler, but the chat could not see or change it.
- Let the model place orders after the guest says "yes": one step shorter,
  but a misread message would commit an order.
- Simulated card payment: adds a form that looks real and proves nothing.

## Consequences
- Cart writes in a chat turn join the turn's transaction. A timed-out turn
  changes nothing.
- Carts and orders are scoped by the session user, like memory.
