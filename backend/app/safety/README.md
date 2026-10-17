# safety

The post-check every recommended item passes before it reaches the user
(CLAUDE.md hard rule 2, ADR 0009).

- `guard.py`: entry point, `check(items, constraints) -> GuardResult(allowed,
  blocked)`. The rule is `HardConstraints.violations` in `menu/constraints.py`
  (contained allergens, "not vegan", "not vegetarian"), shared with `get_item`
  so the model sees the same conflicts the guard enforces. `may_contain` never
  blocks; it becomes a warning on the card.
- What happens to blocked items (one corrective retry, then a fixed safe
  reply) is in `agent/loop.py`.

Tests: `tests/safety/test_guard.py` covers every branch and checks every menu
item against every allergen and diet; `tests/agent/test_loop_safety.py` shows
that a model recommending everything still never gets a violating card, and
that a failed corrective retry still ends in the safe fallback;
`tests/api/test_safety_flow.py` covers stored and just-stated allergies end to end.

Depends on: `menu`. Used by: `agent`.
