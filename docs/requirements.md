# Requirements traceability

Every requirement from the brief, where it is implemented, and how it is
verified. Update the last two columns as phases finish.

## Part 1: Baseline
| # | Requirement (brief section) | Implemented in | Verified by |
|---|---|---|---|
| R1 | Natural conversation gathers preferences, no questionnaire (2.1) | `agent/`, `memory/extract.py` | `tests/memory/test_extract.py`; evals: extraction_precision |
| R2 | Recommendations consider preferences, restrictions, request (2.2) | `agent/`, `tools/search_menu.py`, `menu/constraints.py`, `safety/` | `tests/tools/test_search_menu.py`, `tests/safety/test_guard.py`, `tests/agent/test_loop_safety.py`; evals: diet_compliance, allergen_safety |
| R3 | Grounded in real menu data, nothing invented (2.2) | ID-only answer, `agent/grounding.py`, `safety/`, DB cards | `tests/agent/test_loop.py`; evals: grounding |
| R4 | Memory persists across independent conversations (2.3) | `memory/supersede.py`, `preferences` table | `tests/api/test_memory_flow.py`; evals: memory_recall |
| R5 | Memory meaningfully changes recommendations (2.3) | profile block in `agent/context.py` | `tests/agent/test_context.py`, `tests/api/test_memory_flow.py`; evals: memory_recall |
| R6 | Corrections and changes replace old facts (2.4) | `memory/supersede.py` | `tests/memory/test_supersede.py`, `tests/api/test_memory_flow.py`; evals: preference_update |
| R7 | Returning users identified (2.5) | `users/`, username + PIN, signed cookie | `tests/users/test_service.py`, `tests/api/test_auth.py` |
| R8 | Users' memories isolated (2.5) | `user_id` from session only (`api/deps.py`), queries scoped by it | `tests/api/test_memory_flow.py`, `tests/memory/test_supersede.py`; evals: isolation |
| R9 | Deployed, usable interface (2.6) | `frontend/` on Netlify, backend on Render free (`netlify.toml`, `render.yaml`, ADR 0017) | frontend tests incl. startup gate; live run in `docs/plan.md` phase 6 |

## Menu (section 3)
| # | Requirement | Verified by |
|---|---|---|
| M1 | 12+ items across 3+ categories | `tests/menu/test_seed_data.py`, for every restaurant (six, 15 to 20 items, 4 categories each) |
| M2 | Different prices | `tests/menu/test_seed_data.py` (Corner Table: all distinct, 16 to 85 SAR; options add their own price) |
| M3 | Vegetarian and non-vegetarian | `tests/menu/test_seed_data.py` (every restaurant has vegetarian dishes; Corner Table: 12 veg, 7 vegan, 6 non-veg) |
| M4 | Different spice levels | `tests/menu/test_seed_data.py` (0 to 3 all used) |
| M5 | Explicit ingredients and allergens | `tests/menu/test_seed_data.py`, non-null columns + CHECK on vocabulary (`tests/menu/test_constraints.py`), options included; `tests/menu/test_allergen_lint.py` checks that named sources list their allergen |
| M6 | Overlapping items for comparison and conflicts | documented in `backend/data/README.md` |

## Part 2: Challenge (section 4)
| # | The brief asks | Answered in |
|---|---|---|
| C1 | Problem identification | ADR 0014, `docs/eval-report.md`, README, video |
| C2 | Prioritization | ADR 0014, `docs/eval-report.md` (safety first, worst run), video |
| C3 | Scope and trade-offs, what was left out | ADR 0014, eval report "does not show", README limitations |
| C4 | Execution and validation | `backend/evals/`, `docs/eval-report.md` |

## Deliverables (section 6)
| # | Deliverable | Status |
|---|---|---|
| D1 | Live URL, available through evaluation, test instructions | live at https://restaurant-agent.netlify.app; keep-awake ping; demo accounts in README |
| D2 | Repo with README: local run, architecture, decisions, setup, limitations | README (updated each phase) |
| D3 | No secrets committed | CI secret scan |
| D4 | Video 8 to 12 min: baseline demo, challenge, deep dive, trade-offs, results | not started |
| D5 | Google Drive folder with URL, repo, video, access notes | not started |

## Version 2 (phases 9 to 18, `docs/plan.md`)
| # | Feature | Where | Evidence |
|---|---|---|---|
| V1 | Many restaurants with options, add-ons and removals (phase 10) | ADR 0018, `menu/` (`restaurant.py`, `models.py`, `configure.py`, `constraints.py`), `data/restaurants/`, `tools/context.py` | `tests/menu/test_configure.py`, `test_fit.py`, `tests/safety/test_guard_exhaustive.py`, `tests/tools/test_option_tools.py`, `tests/api/test_restaurants.py`; evals marked phase 10 |
| V2 | Browse, cart and checkout by hand (phase 11) | ADRs 0019, 0021, `app/orders/`, `app/api/cart.py`, `orders.py`, `frontend/src/features/{menu,cart,orders}` | `tests/orders/`, `tests/api/test_cart_api.py`, `test_orders_api.py`; frontend `ItemSheet`, `CartDrawer`, `Checkout` tests |
| V2 | Ordering through the chat (phase 12) | ADRs 0019, 0020, `app/tools/` cart tools, `app/agent/turn_setup.py`, `turn_reply.py`, frontend `ActionCard`, `CheckoutCard` | `tests/tools/test_add_to_cart.py`, `test_cart_edit_tools.py`, `tests/api/test_chat_ordering.py`; `ordering` evals (`evals/cases/ordering.yaml`) |
| V2 | Photos, photo cards and menu blocks (phase 13) | ADR 0024, migration 0005, `backend/scripts/photos/`, `app/tools/show_menu.py`, frontend `DishPhoto`, `MenuBlock`, `useQuickAdd` | `tests/scripts/test_photos.py`, `tests/menu/test_photo_files.py`, `tests/tools/test_show_menu.py`; frontend `DishPhoto`, `MenuBlock`, quick add tests; grounding evals `grounding-show-*` |
| V2 | English voice input (phase 15, English only) | `app/api/transcribe.py`, `app/agent/transcribe.py`, `frontend/src/features/voice/` | `tests/api/test_transcribe.py`; frontend `MicButton` tests |
| V2 | Day rules, calorie goal and estimates, "Matches my tastes" | ADR 0025, migrations 0006 and 0007, `app/menu/taste.py`, `menu/clock.py`, `api/preferences.py` (today), frontend `MemoryPanel`, `MenuBrowser` | `tests/memory/test_day_rules_and_calories.py`, `tests/menu/test_calories.py`, `test_taste.py`, `tests/api/test_menu_tastes.py`; extraction evals `extract-day-rule`, `extract-calorie-goal` |
