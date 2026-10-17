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
    api/          HTTP routes only: auth, chat, conversations, preferences, health;
                  plus the session cookie (session.py) and user_id dependency (deps.py)
    agent/        LLM loop, system prompt, context builder, final-answer schema
    tools/        tools the model can call: search_menu, get_item
    menu/         menu model, queries, filters, allergen vocabulary
    memory/       extract preferences, store them, supersede outdated ones
    safety/       hard-constraint guard for allergens and diet
    users/        users, PIN hashing, login or register
    db/           engine, session dependency, declarative Base
  migrations/     Alembic migrations
  scripts/        seed_menu.py, seed_demo_users.py (both run on every deploy)
  data/menu.json  menu seed data (source of truth for the seed)
  evals/          eval cases, graders, runner, results
  tests/          unit and integration tests, mirroring app/
frontend/
  src/features/chat/    chat window, messages, item cards
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
api -> agent -> tools | memory | safety -> menu | users -> db
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
2. **Load profile**: active preferences for `user_id`.
3. **Extract**: a structured LLM call turns the new message plus the current
   profile into memory operations (`add`, `supersede`, `remove`). Validated by
   Pydantic, applied in one transaction. Runs before the reply so "I'm vegan
   now, what should I get?" is answered with the updated profile. The call
   goes through a `JSONCompleter` that `agent/` injects, so `memory/` never
   imports the SDK.
4. **Build context**: system prompt, then the profile block at the top, then
   the last 20 messages of this conversation. IDs recommended earlier in the
   conversation are noted and may be recommended again without a new search.
   If step 3 changed the profile, a short note saying what changed goes last,
   so the reply confirms it (found by the phase 7 evals, `docs/eval-report.md`).
5. **Agent loop**: the model may call `search_menu` / `get_item`. Hard
   constraints (`menu/constraints.py`, built from the stored profile) are
   merged into every search and can only narrow it. `get_item` still returns
   an item but lists its `conflicts_with_guest`.
   Full tool results go back into context. Loop ends when no tools are called.
6. **Final answer**: structured `{reply, recommended_item_ids}`.
7. **Safety check**: every recommended ID must exist and pass the guard. A
   failing ID is removed and logged, and the model gets one corrective retry
   (whenever any card is blocked, since the reply text would still name it).
   If that still breaks a constraint, the blocked cards are dropped and the
   reply is replaced by a fixed safe message. The guard runs on every card,
   including IDs carried over from earlier in the conversation. Items with a
   `may_contain` allergen the guest avoids pass with a warning on the card.
8. **Persist and respond**: save both messages; return the reply plus item
   cards loaded from the database.

## Data model
- `users`: id, username (unique, lowercase `[a-z0-9_]{3,20}`), pin_hash (argon2), created_at
- `menu_items`: id, name (unique), category, description, price_sar NUMERIC(8,2),
  is_vegetarian, is_vegan, spice_level (0 to 3), ingredients text[],
  allergens text[] (fixed vocabulary), may_contain text[]. CHECK constraints
  enforce the vocabulary, categories, spice range, price > 0 and vegan => vegetarian.
- `conversations`: id, user_id, started_at
- `messages`: id, conversation_id, role, content, recommended_item_ids int[], created_at
- `preferences`: id, user_id, kind, value, status (active, superseded or
  removed), superseded_by, source_message_id, created_at

`kind` is one of: allergy, diet, dislike, like, budget, spice. CHECKs keep
values in their vocabularies (allergens, vegetarian/vegan, none/mild/medium/hot,
a positive SAR amount). Partial unique indexes allow one active diet, budget
and spice per user, and one active row per kind and value.
`is_hard` is derived, not stored: true for allergy and diet only; these are
enforced by `safety/`. Everything else is a soft preference the model weighs.

## Where each guarantee lives
| Guarantee | Enforced in |
|---|---|
| No allergen or diet violation | `HardConstraints.restrict` in `search_menu` + `safety/guard.py` on every card |
| No invented dishes or prices | ID-only answers + DB-rendered cards |
| User isolation | `user_id` from session; never a tool argument |
| Outdated facts replaced | `memory/supersede.py`, status column |
| Facts survive long chats | profile stored in DB, injected every turn |
