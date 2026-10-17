# Handoff (2026-10-17, end of session: v2 phase 11 nearly done)

Read this first in a new session, then `CLAUDE.md` and `docs/plan.md`.

## Where we are
| Phase | State |
|---|---|
| 0 to 8 (v1) | done and live; v1 video moved to phase 18 |
| 9 v2 foundations | done: ADRs 0018 to 0023, v2 plan in `docs/plan.md` |
| 10 Restaurants and options | done and live: 6 restaurants, 103 dishes, 304 options, evals pass |
| 11 Cart and checkout by hand | code, tests, docs and review fixes committed and pushed; **not yet live-checked** |
| 12 to 18 | not started: chat ordering, visuals, mobile, voice, restaurant CRM, personal CRM, final evals and video |

Repo: GitHub `Adi-AdiSendi/restaurant-agent` (private), branch `main`, all
pushed. Commits are allowed (one logical change each). At the end of this
session these were all green locally:
- backend: 806 tests, ruff, pyright and the import layers;
- frontend: 66 tests, ESLint and Prettier;
- the line limits.

Check CI on the last push with `gh run list --limit 1`.

## Phase 11: what exists
- **Backend:**
  - migration 0004 (`carts`, `cart_lines`, `orders`, `order_lines`);
  - `app/orders/` (cart service, checkout with a cart row lock, orders, status by time);
  - routes `app/api/cart.py`, `app/api/orders.py` and `GET /api/restaurants/{slug}/menu`.

  Cart and order errors return a `code` (conflict, other_restaurant,
  invalid_choice, empty_cart, unavailable, not_found).
- **Consent** (ADR 0019): a request carries `accepted_reasons`, the conflict
  reasons the guest was shown. Any other conflict gets a new 409, at add and
  at checkout. Only the checkout button places an order.
- **Chat lock:** the chat turn's user lock is `FOR NO KEY UPDATE`, so carts
  and orders never wait for a chat reply (`tests/orders/test_locks.py`, a
  committed two-session test).
- **Frontend** (react-router 7.18.4):
  - `/` restaurants; `/r/:slug` with the menu, item sheet, and Chat and
    Memory tabs; `/checkout`; `/orders`; `/orders/:id`;
  - a cart button and drawer in the header;
  - chat cards open the same item sheet;
  - `components/useModal.ts` makes the sheet and drawer keyboard-modal.

## Next session: finish phase 11, then phase 12
1. **Live-check phase 11.** The push at the end of this session deployed it;
   the Render build runs migration 0004.
   - Check, on https://restaurant-agent.netlify.app with a fresh user and timed:
     - order a latte with oat milk for pickup;
     - it shows under Orders;
     - another user gets 404 for that order;
     - whole milk with a dairy allergy asks "Add it anyway?".
   - Record the results in the phase 11 status in `docs/plan.md` and mark the phase done.
2. **Review findings left open** (all small):
   - `OrderPage` polling: add a cancelled flag so a response that arrives
     after unmount sets no timer, and reset state when `id` changes (render
     an inner component keyed by `id`).
   - `MenuPage`: key it by `slug` so the tab, search and an open sheet do not
     carry over between restaurants; ignore a stale menu response in
     `useGuestMenu`.
   - Frontend tests for:
     - consent resets when the choice changes;
     - the optional single choice is a checkbox that can be cleared;
     - Escape closes the sheet and drawer.
   - README "Known limitations":
     - the total is charged at the current price, with no check against
       what the guest reviewed;
     - an order does not record that the guest overrode a warning (would
       need migration 0005);
     - a dish removed from the menu drops out of carts silently (FK cascade).
3. **Phase 12, ordering through the chat:** plan it in plan mode first
   (`docs/plan.md` phase 12).
   - Cart tools get the `ToolContext` and call `app/orders` (`add_line`
     etc.) with no `accepted_reasons`, so a conflict is always refused and
     explained.
   - `propose_checkout` shows a card; the guest's button places the order.
   - The reply carries the cart.
   - Add an `ordering` eval category.

## Still open (needs the user)
- **Before the repo goes public:** remove `docs/task/` (the brief PDF, only
  in commit 60cb32b) from history and force-push.
  - The auto-mode classifier blocked the rewrite. The user must run it, or
    allow `git filter-branch` and `git push --force-with-lease` in settings.
  - Steps: copy the PDF somewhere safe, run
    `git filter-branch --index-filter "git rm -r --cached --ignore-unmatch docs/task" -- main`,
    add `docs/task/` to `.gitignore`, re-run gitleaks, and force-push.
  - Commit hashes quoted in `docs/plan.md` will change.
- **Netlify:** delete the backend secrets the user copied into Netlify
  environment variables (only Render needs them).
- **Photos (phase 13):** the user has **no Pexels key**.
  - Options offered:
    - Openverse (no key, Creative Commons, credits; recommended);
    - hand-downloaded Pexels or Unsplash photos;
    - icons only.
  - Pinterest images cannot be used (no licence).
  - Update ADR 0022 once one is chosen.

## Deploy design (ADR 0017, accepted)
- Netlify serves the UI and proxies `/api/*` to FastAPI on Render free
  (`netlify.toml`, `render.yaml`, native uv, no Docker). Netlify DB for Postgres.
- The Render build runs migrations, the menu seed and the demo-user reset.
- 22 s turn deadline (the proxy stops at 26 s). Production DB engine uses NullPool.
- Keep-awake: `frontend/netlify/functions/keep-awake.mts` every 10 min.
- Demo users reset on every Render build: `demo_alice` / 1234, `demo_bob` / 5678.

## Run locally
- `docker compose up -d db` (Docker Desktop must be running).
- `cd backend && uv run alembic upgrade head && uv run python -m scripts.seed_menu`.
- `cd frontend && npm run build`, then `cd backend && uv run uvicorn app.main:app`
  serves everything on http://localhost:8000 (or `npm run dev` on 5173).
- Evals (real model, local DB):
  `cd backend && uv run python -m evals.run --runs 3 [--ids a,b] --label x`.
- `.env` (repo root, gitignored) holds `OPENAI_API_KEY`,
  `OPENAI_MODEL=gpt-6-luna` and `NETLIFY_DB_URL`. Scripts that touch the
  hosted DB must check the host first.

## Gotchas learned
- **Shell:**
  - Heredocs with an apostrophe inside fail in the Bash tool; write a script file instead.
  - Keep a check and its commit on one `&&` chain. A `git commit` on the
    line after a heredoc runs even when the check failed.
- **Python and pytest:**
  - Windows pytest needs the project-local `--basetemp` (already in pyproject).
  - `httpx2` (not `httpx`) is required by the current Starlette test client.
  - DB tests share one rolled-back transaction. A test that needs two real
    transactions commits its own rows and cleans them up (`tests/orders/test_locks.py`).
- **Model:** gpt-6-luna is a reasoning model. Reasoning items are replayed
  between tool rounds with `include=["reasoning.encrypted_content"]` and `store=False`.
- **Hosting limits** (checked 2026-10-17):
  - Netlify proxy rewrites stop at 26 s.
  - Netlify DB Free sleeps after 5 minutes.
  - Render free sleeps after 15 minutes.
- **Menu data:** the JSON in `backend/data/restaurants/` is the source of
  truth; edit it directly. The allergen lint (`tests/menu/test_allergen_lint.py`)
  checks every change.
