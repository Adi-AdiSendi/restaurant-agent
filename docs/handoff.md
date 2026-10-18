# Handoff (2026-10-18: build finished, final session = submission)

Read this first, then `README.md`. The build is done; the last session is
for the video and the submission.

## Where we are
| Phase | State |
|---|---|
| 0 to 8 (v1) | done and live |
| 9 to 13 (v2) | done and live: 6 restaurants with options, cart and checkout, ordering by chat, photos, menu blocks |
| 15 Voice | done and live in English only (mic next to Send) |
| 14, 16, 17 | cut for the deadline by the user: mobile pass, Arabic, both CRMs |
| Extras (2026-10-18) | storefront list, Auto send for voice, day rules, calorie goal and estimates, "Matches my tastes", the chat emptying and refilling the cart, dates in boxes of 3 (ADR 0025, 0019 amended) |
| 18 | left for the final session: video and submission |

Repo: GitHub `Adi-AdiSendi/restaurant-agent` (private), `main`, all pushed.
Live: https://restaurant-agent.netlify.app (UI) proxying to Render. Green at
the end: backend 883 tests, frontend 97, ruff, pyright, import layers, line
limits, CI. Evals (last full run, `phase13-final`): every safety category
passes every run; see `docs/eval-report.md`.

## Final session plan (about 5 hours)
1. **Wake and smoke-test the live site** (Render sleeps; the first load can
   take about 30 s). Log in as `demo_alice` / 1234 and walk the README "Try
   it" steps 1 to 13 once. In Chrome, press the mic and say "Add a small
   latte with oat milk": the text should appear in the box (voice was only
   tested with fakes and the API; this is its first real spoken test).
   If voice fails in Chrome, the fallback is typing; note it in the README.
2. **Video, 8 to 12 minutes** (brief section 6.3). Suggested order:
   - the problem and the stack (README "How it works", one minute);
   - memory: Alice's picks, a correction ("I'm vegan now"), a new chat;
   - safety: the peanut bowl refused; allergens enforced in code
     (`app/safety/`, `search_menu`), never only in the prompt;
   - restaurants with options: Bean & Bloom latte with a dairy allergy;
   - ordering by hand (sheet, "Add it anyway?", checkout) and by chat
     (pickles left out, "make that two", the checkout card);
   - photos and a menu block; voice;
   - evals: the per-category table and the regressions they caught
     (`docs/eval-report.md`: phase 7 update fix, phase 12 dislike, phase 13
     menu blocks);
   - decisions and limits: ADRs, README "Known limitations".
3. **Drive folder** with the video and the repo link, then open every link
   from a logged-out browser.
4. **Optional, before making the repo public:** remove `docs/task/` from the
   git history (steps below). It needs your go-ahead to force-push.
5. Not done for lack of usage: a `code-reviewer` pass on the voice feature
   (commits 3cc1ba0 and 311dc6a). Low risk (login, size cap, rate limit,
   no auto-send), but run it if time allows.

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
