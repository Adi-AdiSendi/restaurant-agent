# Handoff (2026-10-18: v2 phase 13 done, phase 14 next)

Read this first in a new session, then `CLAUDE.md` and `docs/plan.md`.

## Where we are
| Phase | State |
|---|---|
| 0 to 8 (v1) | done and live; v1 video moved to phase 18 |
| 9 to 11 (v2) | done and live: ADRs, 6 restaurants with options, cart and checkout by hand |
| 12 Ordering through the chat | done and live-checked 2026-10-18 (see `docs/plan.md`) |
| 13 Visuals | done and live-checked 2026-10-18: 91 reviewed Openverse photos, menu blocks, quick Add |
| 14 to 18 | not started: mobile, voice, restaurant CRM, personal CRM, final evals and video |

Repo: GitHub `Adi-AdiSendi/restaurant-agent` (private), branch `main`, all
pushed. Commits are allowed (one logical change each). Green at the end of
this session: backend 854 tests, ruff, pyright and the import layers;
frontend 82 tests, ESLint and Prettier; the line limits; CI. The live site
serves bundle `index-CjJDF6BI.js`.

## Phase 12: what exists
- `app/tools/`: `view_cart`, `add_to_cart`, `update_cart_line`,
  `remove_cart_line`, `recent_orders`, `propose_checkout`. Writes go through
  `cart_write.py` (a savepoint); order errors map to tool errors with advice
  (`order_errors.py`); `dislikes.py` matches removable ingredients by words.
- `app/agent/turn_setup.py` builds the turn (cart block after the profile);
  `turn_reply.py` returns `ChatReply` with `actions` and `cart`.
- Checkout takes `expected_total_sar`; a different total is 409
  `cart_changed`. Both the checkout page and the chat card send it
  (`usePlaceOrder`).
- Frontend: `ActionCard`, `orders/CheckoutCard`, `api/errors.ts`.
- Evals: `ordering` category, cart grader, p95 per category.

## Phase 13: what exists
- Photos: `backend/scripts/photos/` (Openverse search with a cache, import,
  credits). Reviewed picks in `backend/data/photos/picks.json`; files in
  `frontend/public/menu/`; `photo` columns (migration 0005). To change a
  photo: edit `picks.json` (A, B, C or none), run
  `uv run python -m scripts.photos.import_photos`, commit.
- `show_menu` tool and menu blocks; quick Add (`features/chat/quickAdd.ts`,
  `features/menu/useQuickAdd.ts`); `components/DishPhoto`, `Skeleton`.

## Next session: phase 14, mobile friendly
Plan it in plan mode first (`docs/plan.md` phase 14). It adds Playwright
(a new dev dependency, needs a reason in the commit) and a manual check on a
real phone.

## Still open (needs the user)
- **Before the repo goes public:** remove `docs/task/` (the brief PDF, only
  in commit 60cb32b) from history and force-push.
  - The auto-mode classifier blocked the rewrite. The user must run it, or
    allow `git filter-branch` and `git push --force-with-lease` in settings.
  - Steps: copy the PDF somewhere safe, run
    `git filter-branch --index-filter "git rm -r --cached --ignore-unmatch docs/task" -- main`,
    add `docs/task/` to `.gitignore`, re-run gitleaks, and force-push.
  - Commit hashes quoted in `docs/plan.md` will change.

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
- **Netlify deploys:** CI green does not mean the site updated. Netlify
  needs no env vars; backend values there fail its secret scan (every UI
  deploy from 623186e to 241823c failed this way). After a push, check the
  live `index.html` asset name or the Netlify deploy list.
- **Hosting limits** (checked 2026-10-17):
  - Netlify proxy rewrites stop at 26 s.
  - Netlify DB Free sleeps after 5 minutes.
  - Render free sleeps after 15 minutes.
- **Menu data:** the JSON in `backend/data/restaurants/` is the source of
  truth; edit it directly. The allergen lint (`tests/menu/test_allergen_lint.py`)
  checks every change.
