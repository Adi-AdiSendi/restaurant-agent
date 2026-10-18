# Architecture

## Overview
Deployed (ADR 0017): Netlify serves the built React app and proxies `/api/*`
to the FastAPI service on Render free, which talks to Netlify DB (Postgres)
and to OpenAI. Locally, FastAPI serves the build itself on one origin.

```
Browser (React) -> Netlify (static build, /api/* proxy) -> FastAPI on Render
                       |                                    |      |
   keep-awake (scheduled): Render /api/health, every 10 min |      +--> OpenAI Responses API
                                                            v
                                     Netlify DB (menu, users, memory, messages)
```

A chat turn has a 22 s deadline because the proxy gives up at 26 s. The UI
waits on `/api/health` while a sleeping backend wakes up.

## Folder map
```
backend/
  app/
    main.py       creates the FastAPI app, mounts routes and the frontend build
    config.py     settings from env (pydantic-settings)
    api/          HTTP routes only: auth, chat, conversations, restaurants (and a
                  guest's menu), preferences, cart, orders, health; plus the session
                  cookie (session.py) and the user and constraints dependencies (deps.py)
    agent/        LLM loop, system prompt, context builder, final-answer schema
    tools/        tools the model can call (menu search and lookup, cart changes,
                  recent orders, propose checkout) and the server-built
                  ToolContext they receive (ADR 0020)
    menu/         restaurants, menu items and options, queries, filters, the fit
                  rule, the order resolver (configure.py), allergen vocabulary
    memory/       extract preferences, store them, supersede outdated ones
    orders/       the cart, checkout and orders, priced by menu/configure.py (ADR 0019)
    safety/       hard-constraint guard for allergens and diet
    users/        users, PIN hashing, login or register
    db/           engine, session dependency, declarative Base
  migrations/     Alembic migrations
  scripts/        seed_menu.py (+ menu_sync.py), seed_demo_users.py (both run on every deploy);
                  photos/ (dev only: Openverse search, import, credits; ADR 0024)
  data/restaurants/  one menu file per restaurant (source of truth for the seed)
  evals/          eval cases, graders, runner, results
  tests/          unit and integration tests, mirroring app/
frontend/
  src/App.tsx           startup gate, login, then routes (React Router, ADR 0021)
  src/features/shell/   header on every page (nav, cart button, log out)
  src/features/restaurants/  home page: the restaurant grid
  src/features/menu/    /r/:slug: menu, item sheet, chat and memory tabs
  src/features/cart/    cart state (server truth), drawer, lines
  src/features/orders/  /checkout, /orders, /orders/:id
  src/features/chat/    chat panel, messages, item cards with their options
  src/features/login/   username + PIN entry
  src/features/memory/  "What I remember about you" panel
  src/features/startup/ "Starting the server" while the backend wakes up
  netlify/functions/    keep-awake scheduled function
  src/api/              backend client and payload types
docs/             architecture, plan, requirements, decisions, eval report
scripts/          repo-wide checks (line limits)
```
Each top-level folder has a short README: what is here, the entry point, what
it depends on. ORM models live in their feature folder (`menu/models.py`), so a
table's CHECK constraints can use that feature's vocabulary without `db`
importing upward.

## Dependency direction
```
api -> agent -> tools | memory | safety -> orders -> menu | users -> db
```
Lower layers never import higher ones. Enforced with import-linter in CI.
`tools`, `memory` and `safety` are siblings and do not import each other.
The hard-constraint type lives in `menu`; `agent` loads it from the profile
and passes it to `search_menu` and to the `safety` post-check.

## One chat turn
Orchestrated by `agent/chat_turn.py` in one transaction; any failure rolls the
whole turn back. The turn has a 22 s deadline (the Netlify proxy stops at 26 s);
past it the turn is rolled back and the API returns 504.

1. `POST /api/chat {conversation_id, message}`. The session cookie gives `user_id`.
   The conversation must belong to that user; it fixes the restaurant
   (`POST /api/conversations {restaurant}` chose it).
2. **Load profile**: active preferences for `user_id`.
3. **Extract**: a structured LLM call turns the new message plus the current
   profile into memory operations (`add`, `supersede`, `remove`). Validated by
   Pydantic, applied in one transaction. Runs before the reply so "I'm vegan
   now, what should I get?" is answered with the updated profile. The call
   goes through a `JSONCompleter` that `agent/` injects, so `memory/` never
   imports the SDK.
4. **Build context**: system prompt (for this restaurant: its name, cuisine and
   categories, and the other restaurants as suggestions it cannot search),
   then the profile block at the top, then
   the guest's cart with each line's id, then
   the last 20 messages of this conversation. IDs recommended earlier in the
   conversation are noted and may be recommended again without a new search.
   If step 3 changed the profile, a short note saying what changed goes last,
   so the reply confirms it (found by the phase 7 evals, `docs/eval-report.md`).
5. **Agent loop**: the model may call `search_menu` / `get_item`. Each gets a
   `ToolContext` built by the server (session, user, conversation, restaurant,
   hard constraints), so every read is scoped to this restaurant. Hard
   constraints (`menu/constraints.py`, built from the stored profile) are
   merged into every search and can only narrow it, and items that no choice
   of options makes safe are dropped. Every option carries its own
   `conflicts_with_guest`; `get_item` still returns a conflicting item but
   lists why.
   Cart tools (`view_cart`, `add_to_cart`, `update_cart_line`,
   `remove_cart_line`, `recent_orders`, `propose_checkout`) call `app/orders`
   for the session's user, each write in a savepoint of the turn's
   transaction. They never pass consent, so a conflicting add is refused and
   explained (ADR 0019); a disliked removable ingredient is left out. No tool
   places an order. `show_menu(category)` returns every dish in a category,
   each with its own conflicts, for a menu block; showing is not
   recommending.
   Full tool results go back into context. Loop ends when no tools are called.
6. **Final answer**: structured `{reply, recommended_item_ids}`.
7. **Safety check**: every recommended ID must exist in this restaurant and
   pass the guard: the base must fit, and every required option group must
   keep a fitting choice (`item_violations`). A
   failing ID is removed and logged, and the model gets one corrective retry
   (whenever any card is blocked, since the reply text would still name it).
   If that still breaks a constraint, the blocked cards are dropped and the
   reply is replaced by a fixed safe message. The guard runs on every card,
   including IDs carried over from earlier in the conversation. Items with a
   `may_contain` allergen the guest avoids pass with a warning on the card.
8. **Persist and respond**: save both messages; return the reply, item cards
   loaded from the database, action cards built from the cart tools' results
   (never from model text), menu blocks from `show_menu` results, and the cart
   as it is after the turn. The UI sets
   its cart from it; a checkout card's button places the order through
   `POST /api/orders`.

## Data model
- `users`: id, username (unique, lowercase `[a-z0-9_]{3,20}`), pin_hash (argon2), created_at
- `restaurants`: id, slug (unique), name (unique), cuisine, tagline,
  accent_color, categories text[] (in menu order), position (ADR 0018),
  photo (nullable `<restaurant>/<name>`, ADR 0024)
- `menu_items`: id, restaurant_id, name (unique per restaurant), category (one
  of the restaurant's, checked by the seed), description, price_sar
  NUMERIC(8,2), is_vegetarian, is_vegan, spice_level (0 to 3), ingredients
  text[], allergens text[] (fixed vocabulary), may_contain text[], removable
  text[] (a subset of ingredients), photo (nullable `<restaurant>/<name>`:
  the UI loads `/menu/<photo>-{320,640}.webp`). The item's own fields
  describe its base.
  CHECK constraints enforce the vocabulary, spice range, price > 0, vegan =>
  vegetarian and removable <@ ingredients.
- `option_groups`: id, item_id, name (unique per item), min_choices,
  max_choices, position
- `options`: id, group_id, name (unique per group), price_delta_sar (>= 0),
  allergens, may_contain, is_vegetarian, is_vegan, spice_level, position. A
  chosen option adds its allergens and can make a dish non-vegetarian;
  removing an ingredient never removes an allergen (`menu/configure.py`).
- `conversations`: id, user_id, restaurant_id, started_at
- `carts`: id, user_id (unique: one open cart per user), restaurant_id, updated_at
- `cart_lines`: id, cart_id, item_id, quantity (1 to 20), option_ids int[],
  removed text[], created_at. No price: it is computed on every read.
- `orders`: id, user_id, restaurant_id, fulfilment (pickup or dine_in),
  total_sar, placed_at
- `order_lines`: id, order_id, item_id (kept null if the dish leaves the
  menu), item_name, category, quantity, unit_price_sar, option_names,
  removed, allergens: a snapshot of what was bought
- `messages`: id, conversation_id, role, content, recommended_item_ids int[], created_at
- `preferences`: id, user_id, kind, value, status (active, superseded or
  removed), superseded_by, source_message_id, created_at

`kind` is one of: allergy, diet, dislike, like, budget, spice. CHECKs keep
values in their vocabularies (allergens, vegetarian/vegan, none/mild/medium/hot,
a positive SAR amount). Partial unique indexes allow one active diet, budget
and spice per user, and one active row per kind and value.
`is_hard` is derived, not stored: true for allergy and diet only; these are
enforced by `safety/`. Everything else is a soft preference the model weighs.

## Ordering by hand (phase 11)
1. `GET /api/restaurants/{slug}/menu`: every dish as `GuestItem`, with what
   conflicts with this guest's saved allergies and diet.
2. `POST /api/cart/lines {restaurant, item_id, quantity, option_ids, removed}`:
   the server resolves the choice (`menu/configure.py`), refuses an invalid
   one (422), and asks for consent (409 `conflict`, or `other_restaurant`
   when the cart is elsewhere). The cart row is locked for the write.
3. Every cart read re-prices and re-checks each line against today's menu;
   a line whose options changed is marked unavailable.
4. `POST /api/orders {fulfilment}`: locks the cart, checks it all again
   (the profile may have changed), snapshots names, options, removals,
   allergens and prices into `order_lines`, and empties the cart. No payment;
   status (placed, preparing, ready) comes from the time since placing.

## Where each guarantee lives
| Guarantee | Enforced in |
|---|---|
| No allergen or diet violation | `HardConstraints.restrict` in `search_menu` + `safety/guard.py` on every card, options included |
| No invented dishes or prices | ID-only answers + DB-rendered cards |
| One restaurant per chat | every menu read takes the conversation's `restaurant_id` from `ToolContext` |
| User isolation | `user_id` from session; never a tool argument; every cart and order query filters by it |
| Prices are real | cart and order prices come from `menu/configure.py`; the request has no price field |
| Only the guest orders | `POST /api/orders` from the checkout button; conflicts need the guest's explicit consent |
| Outdated facts replaced | `memory/supersede.py`, status column |
| Facts survive long chats | profile stored in DB, injected every turn |
