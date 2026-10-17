# tools

Tools the model can call. One file per tool, each with `NAME`, `DESCRIPTION`,
`PARAMETERS` (strict JSON schema) and `handle(session, arguments_json, constraints)`.

- `search_menu.py`: menu search with SQL filters. The guest's hard
  constraints are merged in with `HardConstraints.restrict`, so the model's
  arguments can only narrow the search. The result reports
  `guest_constraints_applied`. No match is `{"items": []}`.
- `get_item.py`: one item by ID, with `conflicts_with_guest` and
  `may_contain_warnings`, or a `not_found` error. The agent may describe a
  conflicting item but the safety post-check blocks it as a recommendation.
- `errors.py`: the shared `{error_category, retryable, message}` shape.
  Bad arguments are `invalid_arguments` and not retryable.

Rules: handlers never take a `user_id`. `constraints` come from the stored
profile via `agent`, never from the model.

Depends on: `menu`. Used by: `agent/tool_dispatch.py`.
