# tools

Tools the model can call. One file per tool, each with `NAME`, `DESCRIPTION`,
`PARAMETERS` (strict JSON schema) and `handle(arguments_json, context)`.

- `context.py`: `ToolContext` (ADR 0020). The agent builds it each turn from
  the session and the stored conversation: DB session, user, conversation,
  restaurant and its categories, and the guest's hard constraints. Nothing
  in it comes from the model.
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
- `menu_views.py`: `ToolItem`, the item as the model sees it: every field,
  and every option with its own `conflicts_with_guest`.
- `errors.py`: the shared `{error_category, retryable, message}` shape.
  Bad arguments are `invalid_arguments` and not retryable.

Rules: tool schemas never contain a user, conversation or restaurant; those
come from the context.

Depends on: `menu`. Used by: `agent/tool_dispatch.py`.
