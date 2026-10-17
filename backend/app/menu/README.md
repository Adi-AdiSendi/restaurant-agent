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
  narrow it. `violations` checks anything with allergens and diet flags;
  `item_violations` is the rule the safety post-check enforces (the base
  fits, and every required group keeps a fitting choice).
- `guest_view.py`: `GuestItem`, an item as one guest sees it (conflicts and
  trace warnings for the item and every option). Tools, chat cards and the
  menu page all use it.
- `configure.py`: the pure resolver. Item + option IDs + removals give the
  unit price, allergens, may-contain, diet flags and spice of that order, or
  a `ConfigurationError`. Removing an ingredient never removes an allergen.

Depends on: `db` (Base). Used by: `tools`, `safety`, `memory`, `scripts/seed_menu.py`.
