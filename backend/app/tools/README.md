# tools

Tools the model can call. One file per tool, each with `NAME`, `DESCRIPTION`,
`PARAMETERS` (strict JSON schema) and `handle(arguments_json, context)`.

- `context.py`: `ToolContext` (ADR 0020). The agent builds it each turn from
  the session and the stored conversation: DB session, user, conversation,
  restaurant (ID, slug, categories), the guest's hard constraints and their
  soft dislikes. Nothing in it comes from the model.
- `search_menu.py`: search this restaurant's menu with SQL filters. The
  guest's hard constraints are merged in with `HardConstraints.restrict`, so
  the model's arguments can only narrow the search, and items that no choice
  of options makes safe are dropped. An unknown category is
  `invalid_arguments` listing this restaurant's categories. The result
  reports `guest_constraints_applied`. No match is `{"items": []}`.
- `get_item.py`: one item of this restaurant by ID, with
  `conflicts_with_guest` and `may_contain_warnings`, or a `not_found` error
  (also for another restaurant's ID). The agent may describe a conflicting
  item but the safety post-check blocks it as a recommendation.
- `show_menu.py`: every dish in one of this restaurant's categories, each
  with its own conflicts, for a menu block in the chat (phase 13). Showing
  is not recommending; recommended IDs still pass the guard.
- Cart tools (phase 12, ADR 0019), each calling `app/orders` for the
  session's user:
  - `view_cart.py`, `recent_orders.py` (the last 3 orders, with lines);
  - `add_to_cart.py`: no consent and no cart replacement are ever passed, so
    a conflict with allergies or diet, or a cart at another restaurant, is
    refused. Removable ingredients the guest dislikes are left out
    (`dislikes.py`), unless the guest keeps them this time;
  - `update_cart_line.py`, `remove_cart_line.py`: by line id, own lines only;
  - `propose_checkout.py`: returns the cart for a checkout card. No tool can
    place an order or empty a cart.
  - `cart_write.py` runs each write in a savepoint, so a refused write
    changes nothing and the turn goes on. `cart_results.py` holds the result
    models; each carries the whole cart.
- `errors.py`: the shared `{error_category, retryable, message}` shape.
  Bad arguments are `invalid_arguments` and not retryable. `order_errors.py`
  maps order errors to it, with what the model should tell the guest.

Rules: tool schemas never contain a user, conversation or restaurant; those
come from the context.

Items come back as `menu/guest_view.py` `GuestItem`s: every field, every
option with its own conflicts and trace warnings.

Depends on: `menu`, `orders`. Used by: `agent/tool_dispatch.py`.
