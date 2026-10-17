# Handoff (2026-10-17, phase 6 in progress)

Read this first in a new session, then `CLAUDE.md` and `docs/plan.md`.

## Where we are
| Phase | State |
|---|---|
| 0 to 5 | done, reviewed, committed |
| 6 Deploy | code, config and docs done and reviewed; **live spike not run** |
| 7 Evals (Part 2) | not started |
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
1. The user creates: the Netlify project (import the repo), the Netlify DB
   (Frankfurt if offered; copy the direct connection string into `.env` as
   `NETLIFY_DB_URL`), and a Render Blueprint (paste `DATABASE_URL`,
   `OPENAI_API_KEY`). Then fix the Render hostname in `netlify.toml` if needed.
2. Run the spike checklist in `docs/plan.md` phase 6 step 9. If Netlify DB is
   not reachable from Render, switch to Neon free and record it in ADR 0017.
3. Live checks from a fresh browser; time 10 turns, record p95 in plan.md.
4. Mark phase 6 done in plan.md and requirements D1. Then phase 7.

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
