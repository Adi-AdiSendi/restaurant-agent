# menu

The menu table and every read of it.

- `allergens.py`, `categories.py`: fixed vocabularies. Changing either needs a
  hand-written migration for the CHECK constraints (autogenerate misses them);
  `tests/menu/test_vocabulary_in_db.py` fails until it exists.
- `models.py`: `MenuItem` ORM model with CHECK constraints.
- `schemas.py`: `MenuItemFields` (seed input), `MenuItemOut` (output), `MenuFilter`.
- `queries.py`: entry point. `search_items`, `get_item`, `get_items_by_ids`.
  All filtering is SQL. "May contain" allergens are not filtered here; the
  safety layer warns about them.
- `constraints.py`: `HardConstraints` (allergens, vegetarian, vegan) built
  from the stored profile. `restrict` merges it into a search and can only
  narrow it; `violations` is the rule the safety post-check enforces.

Depends on: `db` (Base). Used by: `tools`, `safety`, `memory`, `scripts/seed_menu.py`.
