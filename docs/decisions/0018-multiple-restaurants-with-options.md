# 0018: Multiple restaurants, with options and add-ons

- Status: Accepted
- Date: 2026-10-17
- Extends: 0009 (hard constraints), 0010 (grounding)

## Context
v2 shows the range of businesses Foodics serves: a burger house, a shawarma
grill, Chinese, seafood, a cafe, and the original Corner Table. Real menus
have choices (bread, size, milk, protein), paid extras and removable
ingredients ("no pickles"). v1 has one flat menu: names unique across the
table, a closed category enum, and a fixed allergen list per item.

## Decision
- A `restaurants` table. Every menu item belongs to one restaurant. Names are
  unique per restaurant. Categories are defined per restaurant, not by a
  global enum.
- One data file per restaurant (`backend/data/restaurants/<slug>.json`). The
  seed upserts by (restaurant, name) and never touches another restaurant.
- Options: an item has option groups (name, min, max choices). An option has a
  price change, allergens, may-contain traces and its own diet flags. An item
  lists the ingredients a guest may remove.
- One pure resolver (`menu/configure.py`) turns item + options + removals into
  the configuration that is priced, checked and shown: unit price, allergens,
  may-contain, vegetarian, vegan, spice. Everything else (cards, cart, guard,
  orders) uses its result.
- Removing an ingredient never removes an allergen. Kitchens share surfaces,
  and a wrong "safe" is the failure that hurts someone.
- Grounding covers options: an option ID is accepted only if it belongs to
  that item.
- The guest picks a restaurant first. Menu, cart and chat are scoped to it.
  The chat may suggest another restaurant by name.

## Alternatives considered
- Options as separate menu items ("Burger with cheese"): no new tables, but
  the menu explodes and choices like milk type cannot be expressed.
- Removal clears an allergen ("no cheese" makes it dairy-free): friendlier,
  but promises more than a kitchen can guarantee.
- One food-court cart across brands: more to show, but splits orders per
  kitchen and complicates prices and safety. Not needed to make the point.

## Consequences
- The guard checks resolved configurations, so an add-on can block a dish.
- The v1 menu stays as Corner Table, unchanged, so its tests and evals keep
  working.
- `price_sar` naming stays: every restaurant prices in SAR.
