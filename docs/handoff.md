# Handoff (2026-10-17, v1 done, v2 phase 9)

Read this first in a new session, then `CLAUDE.md` and `docs/plan.md`.

## Where we are
| Phase | State |
|---|---|
| 0 to 5 | done, reviewed, committed |
| 6 Deploy | done: live at https://restaurant-agent.netlify.app, cold start and DB sleep measured |
| 7 Evals (Part 2) | done: 42 cases x 3 runs, `docs/eval-report.md` |
| 8 Submission | README rewritten for reviewers; video moved to phase 18 |
| 9 to 18 (v2) | planned in `docs/plan.md`, ADRs 0018 to 0023; phase 9 in progress |

Repo: private GitHub `Adi-AdiSendi/restaurant-agent`, branch `main`, CI green.
Commits are allowed now (one logical change each); see ADR 0017 for the deploy.

## v2 in one paragraph
Six restaurants with options, a server cart and orders (chat can edit the
cart, only the guest's button places an order), photo cards, a mobile pass,
voice in English and Arabic, a staff CRM and a personal CRM on simulated
history. The sibling apps have no cart: reuse their patterns (see the v2
overview in plan.md), not their code.

## Deploy design (ADR 0017, accepted)
- Netlify serves the UI and proxies `/api/*` to FastAPI on Render free
  (`netlify.toml`, `render.yaml`, native uv, no Docker). Netlify DB for Postgres.
- 22 s turn deadline (proxy stops at 26 s). Production DB engine uses NullPool.
- Keep-awake: `frontend/netlify/functions/keep-awake.mts` every 10 min.
- UI startup gate: `frontend/src/features/startup/`.
- Demo users reset on every Render build: `demo_alice` / 1234, `demo_bob` / 5678.

## Next steps
1. Done: Netlify project `restaurant-agent` (was `jovial-gelato-6307c0`)
   with Netlify DB (us-east-2); Render Blueprint `restaurant-agent-api` in Ohio.
   Live run passed, p95 7.5 s (see plan.md phase 6). Local `.env` has the DB
   string as `NETLIFY_DB_URL`; scripts that touch it must check the host.
2. Done: keep-awake fixed (it now pings Render directly), cold start
   measured (ready at 33.5 s, first turn 7.7 s), DB sleep confirmed; see
   plan.md phase 6 step 11. The user should still delete the backend
   secrets they copied into Netlify env vars (only Render needs them).
3. The ping was paused for the test and restored (commit 2b068f4).
4. Phase 7 is done (`docs/eval-report.md`): three fixes to the memory-change
   note, the third after the code review found the first two shortened
   replies. Final run `after-3`: every case passes; dead ends 11/159.
5. Phase 8, remaining (plan in `~/.claude/plans/we-stoped-at-phase-spicy-pebble.md`):
   - Before the user makes the repo public: remove `docs/task/` (the brief
     PDF, only in commit 60cb32b) from history with filter-branch, force-push,
     add it to `.gitignore`, re-run gitleaks. Commit author email is public.
   - `docs/submission.md` for the Drive folder; anonymous link check.
   - Video later: the user wants more changes once the core is solid.

## Run locally
- `docker compose up -d db` (Docker Desktop must be running)
- `cd backend && uv run alembic upgrade head && uv run python -m scripts.seed_menu`
- `cd frontend && npm run build`, then `cd backend && uv run uvicorn app.main:app`
  serves everything on http://localhost:8000 (or `npm run dev` on 5173).
- `scripts.seed_demo_users` deletes and recreates the demo users; locally they
  hold history from real-model runs, so do not run it there unless intended.
- `.env` (repo root, gitignored) holds `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-6-luna`.

## Gotchas learned
- Shell heredocs with an apostrophe inside fail in the Bash tool; write files instead.
- Windows pytest needs the project-local `--basetemp` (already in pyproject).
- `httpx2` (not `httpx`) is required by the current Starlette test client.
- gpt-6-luna is a reasoning model: reasoning items are replayed between tool
  rounds with `include=["reasoning.encrypted_content"]` and `store=False`.
- Real-model runs write to the dev DB; tests must scope counts to their own rows.
- Netlify facts checked 2026-10-17: functions are JS/TS/Go only, 60 s sync
  limit; proxy rewrites stop at 26 s; Netlify DB Free sleeps after 5 min, 48
  compute hours per billing period. Render free sleeps after 15 min, 750 h/month.

## Phase 7 eval ideas already noted
- Reply text that names a blocked dish as a pick (guard checks IDs, not text).
- The model offering to "include non-vegetarian dishes" to a vegetarian.
- Extraction precision ("my friend is vegan"), corrections, isolation.
