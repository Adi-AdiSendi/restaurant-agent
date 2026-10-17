# data

`restaurants/<slug>.json` holds one file per restaurant, and each file is the
source of truth for that restaurant's menu (`scripts/seed_menu.py`). The file
name must match the slug. Every restaurant is fictional, and all prices are
in SAR. Allergens use the fixed vocabulary in `app/menu/allergens.py`.

Each file has the restaurant's name, cuisine, tagline, accent colour and
ordered categories, then its items. An item may list `removable` ingredients
and `option_groups` (with `min_choices` and `max_choices`). Each option has
its own price change, allergens, may-contain, diet flags and spice level.
Allergen and diet fields are always written out, never defaulted.

## Corner Table (`corner-table.json`, the v1 menu)
18 items in 4 categories: starters, burgers and mains, bowls and pasta,
desserts and drinks. Prices run from 16 to 85 SAR. 12 vegetarian items, 7 of
them vegan, and 6 with meat or fish. Spice levels 0 to 3.

## Overlaps designed for comparisons and conflicts (brief M6)
| Pair or group | What it tests |
|---|---|
| Pesto Penne vs Penne Arrabbiata | Same pasta. Tree-nut allergy must rule out pesto (pine nuts); arrabbiata is vegan but spicy (2). |
| Thai Peanut Noodle Bowl vs Mediterranean Veggie Bowl | Both vegan bowls. Peanut allergy or "no spice" removes the Thai bowl. |
| Classic Smash Burger (52) vs Double Wagyu Burger (85) | Same allergens, big price gap. Tests budget. |
| Plant-Based Burger vs both beef burgers | The vegan answer to "I want a burger". Soy allergy rules it out. |
| Buffalo Wings, Nashville Hot Chicken | Spice 3 non-veg items for "I love spicy" vs "nothing hot". |
| Chocolate Lava Cake | Only "may contain" item (tree nut): a warning, not a hard block. |
| Pistachio Cheesecake vs Mango Sorbet | Tree nut and dairy vs an allergen-free vegan dessert. |
| Shrimp Poke Bowl | Shellfish, plus hidden egg and gluten in the mayo and soy sauce. |
| Edamame, Plant-Based Burger, Thai bowl, Poke bowl | Soy appears across categories, so a soy allergy narrows several choices at once. |

Conflicting requests these support: "vegan, nut-free and spicy" (only Edamame,
Plant-Based Burger and Penne Arrabbiata fit), "vegetarian main under 40 SAR"
(only the Mediterranean Veggie Bowl), "dairy-free dessert" (only the sorbet;
Fresh Lemon Mint is a drink).
