# menu

Restaurants, their menus and options, and every read of them.

- `allergens.py`: the fixed allergen vocabulary, and `ALLERGENS_SQL` for the
  CHECK constraints. Changing it needs a hand-written migration (autogenerate
  misses CHECKs); `tests/menu/test_vocabulary_in_db.py` fails until it exists.
- `restaurant.py`: the `Restaurant` table, and the slug, colour and category
  patterns. Each restaurant lists its own categories, in menu order.
- `models.py`: `MenuItem`, `OptionGroup`, `Option`, with CHECK constraints.
  An item's own allergens and diet flags describe its base; an option adds
  its own. Groups and options load with their item.
- `schemas.py`: `MenuItemFields` (seed input), `MenuItemOut` (output, with
  option groups), `MenuFilter`. `option_schemas.py`: groups and options.
  `restaurant_schemas.py`: `RestaurantFile` (one data file) and `RestaurantOut`.
- `queries.py`: entry point. `search_items`, `get_item`, `get_items_by_ids`,
  `list_restaurants`, `restaurant_by_slug`. All filtering is SQL. "May
  contain" allergens are not filtered here; the safety layer warns about them.
- `constraints.py`: `HardConstraints` (allergens, vegetarian, vegan) built
  from the stored profile. `restrict` merges it into a search and can only
  narrow it; `violations` is the rule the safety post-check enforces.

Depends on: `db` (Base). Used by: `tools`, `safety`, `memory`, `scripts/seed_menu.py`.
