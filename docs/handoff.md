# Handoff (2026-10-17, phase 7 done)

Read this first in a new session, then `CLAUDE.md` and `docs/plan.md`.

## Where we are
| Phase | State |
|---|---|
| 0 to 5 | done, reviewed, committed |
| 6 Deploy | **live** at https://restaurant-agent.netlify.app; two checks left |
| 7 Evals (Part 2) | done: 42 cases x 3 runs, `docs/eval-report.md` |
| 8 Submission | not started |

Repo: private GitHub `Adi-AdiSendi/restaurant-agent`, branch `main`, CI green.
Commits are allowed now (one logical change each); see ADR 0017 for the deploy.

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
2. Left: observe a cold start after a missed ping, and that the DB sleeps
   when idle (Netlify DB usage page). The user should delete the backend
   secrets they copied into Netlify env vars (only Render needs them).
3. Then mark phase 6 done in plan.md.
4. Phase 7 is done (`docs/eval-report.md`). The memory-change note fix is
   committed and pushed; Render redeploys on push, so the live site has it.
5. Next: phase 8 (submission): README pass, video 8 to 12 min, Drive folder,
   check every link from a logged-out browser.

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
