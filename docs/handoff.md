# Handoff (2026-10-18: v2 phase 11 done, phase 12 next)

Read this first in a new session, then `CLAUDE.md` and `docs/plan.md`.

## Where we are
| Phase | State |
|---|---|
| 0 to 8 (v1) | done and live; v1 video moved to phase 18 |
| 9 v2 foundations | done: ADRs 0018 to 0023, v2 plan in `docs/plan.md` |
| 10 Restaurants and options | done and live: 6 restaurants, 103 dishes, 304 options, evals pass |
| 11 Cart and checkout by hand | done and live-checked through the API on 2026-10-18 |
| 12 to 18 | not started: chat ordering, visuals, mobile, voice, restaurant CRM, personal CRM, final evals and video |

Repo: GitHub `Adi-AdiSendi/restaurant-agent` (private), branch `main`, all
pushed. Commits are allowed (one logical change each). Green locally at the
end of this session: backend 806 tests, ruff, pyright and the import layers;
frontend 73 tests, ESLint and Prettier; the line limits. Check CI on the last
push with `gh run list --limit 1`.

## Phase 11: what exists
- **Backend:** migration 0004 (`carts`, `cart_lines`, `orders`,
  `order_lines`); `app/orders/` (cart service, checkout with a cart row
  lock, orders, status by time); routes `app/api/cart.py`, `app/api/orders.py`
  and `GET /api/restaurants/{slug}/menu`. Cart and order errors return a
  `code` (conflict, other_restaurant, invalid_choice, empty_cart,
  unavailable, not_found).
- **Consent** (ADR 0019): a request carries `accepted_reasons`, the conflict
  reasons the guest was shown. Any other conflict gets a new 409, at add and
  at checkout. Only the checkout button places an order.
- **Chat lock:** the chat turn's user lock is `FOR NO KEY UPDATE`, so carts
  and orders never wait for a chat reply (`tests/orders/test_locks.py`).
- **Frontend** (react-router 7.18.4): `/` restaurants; `/r/:slug`
  (`MenuRoute` keys `MenuPage` by slug) with the menu, item sheet, and Chat
  and Memory tabs; `/checkout`; `/orders`; `/orders/:id` (`OrderView` keyed
  by id). A cart button and drawer in the header; chat cards open the same
  item sheet; `components/useModal.ts` makes the sheet and drawer modal.
- **Live check script:** an API flow with two fresh users, timed (results in
  `docs/plan.md`). It lived in the session scratchpad; rewrite it from the
  table there if needed. The browser click-through was not done (Claude in
  Chrome was not connected); worth a manual pass.

## Next session: phase 12, ordering through the chat
Plan it in plan mode first (`docs/plan.md` phase 12).
- Cart tools get the `ToolContext` (`app/tools/context.py`) and call
  `app/orders` (`add_line` etc.) with no `accepted_reasons`, so a conflict is
  always refused and explained. Register them in `app/agent/tool_dispatch.py`.
- `propose_checkout` shows a card; the guest's button places the order.
- The reply (`app/agent/schemas.py` `AgentReply`) carries the cart; the
  drawer updates from it.
- Add an `ordering` eval category; measure p95 turn time against 22 s.

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
