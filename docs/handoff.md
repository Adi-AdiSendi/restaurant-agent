# Handoff (2026-10-17)

Read this first in a new session, then `CLAUDE.md` and `docs/plan.md`.

## Where we are
9 phases (0 to 8). **Phases 0 to 5 are done**, each reviewed by the
`code-reviewer` agent and fixed. **Current phase: 6 (deploy), replanned for
Netlify, not started.** No code has been written for phase 6.

| Phase | State |
|---|---|
| 0 Scaffold | done (CI written but never run: no commits yet) |
| 1 Menu and DB | done: 18 items, CHECK constraints, idempotent seed |
| 2 Agent and tools | done: Responses API loop, grounding by ID |
| 3 Users and memory | done: username + PIN, extraction, supersession |
| 4 Safety guard | done: allergens/diet enforced in search and on every card |
| 5 Frontend | done: Foodics brand, cards, memory panel |
| 6 Deploy | **replanned for Netlify** (see plan.md, ADR 0017 Proposed) |
| 7 Evals (Part 2) | not started |
| 8 Submission | not started |

Checks at handoff: backend 233 tests, pyright strict 0 errors, ruff clean,
import contract kept; frontend 27 tests, lint and typecheck clean, build OK;
line limits OK.

## Decisions the user still has to make
1. **Backend host for phase 6.** Netlify cannot run FastAPI. Recommended:
   an always-on container host (Fly.io or Render paid) for the existing
   Docker image, behind a Netlify `/api/*` proxy. Railway for the backend only
   is possible but the user moved away from Railway.
2. **Database**: Netlify DB (Neon) recommended, or Neon directly.
3. **Accept ADR 0017** (then mark ADR 0006 superseded, both linked).
4. **Commits**: the user said "we will not commit" for now. Git is
   initialized, nothing committed, no remote. Netlify deploys from git or
   from the CLI (`netlify deploy`); ask which before phase 6.

## Next steps (phase 6, in order)
1. Spike: confirm the Netlify 200-proxy passes `Set-Cookie` and the cookie
   comes back. Everything else depends on it.
2. `netlify.toml` (base `frontend`, publish `dist`, `/api/*` proxy, SPA
   fallback); remove `railway.toml`; DB URL with `?ssl=require`.
3. Turn deadline (~22 s, under the 26 s proxy timeout) with a clear 504.
4. Migrations + seed on backend release; seed `demo_alice` / `demo_bob`.
5. Update CLAUDE.md stack line, architecture overview, README, requirements.

## Run locally
- `docker compose up -d db` (Docker Desktop must be running)
- `cd backend && uv run alembic upgrade head && uv run python -m scripts.seed_menu`
- `cd frontend && npm run build` then `cd backend && uv run uvicorn app.main:app`
  serves everything on http://localhost:8000 (or `npm run dev` for the UI on 5173).
- Local demo users (from real-model runs): `demo_alice` / PIN `1234`
  (peanut allergy, vegetarian, mild spice; "hot" superseded) and
  `demo_bob` / `5678` (empty profile). They exist only in the local DB.
- `.env` (repo root, gitignored) holds `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-6-luna`.

## Gotchas learned
- Shell heredocs with an apostrophe inside fail in this environment's Bash
  tool. Write scripts or files with the Write tool instead.
- Windows pytest needs the project-local `--basetemp` (already in pyproject).
- `httpx2` (not `httpx`) is required by the current Starlette test client.
- gpt-6-luna is a reasoning model: reasoning items are replayed between tool
  rounds with `include=["reasoning.encrypted_content"]` and `store=False`.
- DB tests run in a rolled-back transaction, but real-model runs write to the
  dev DB; tests must scope counts to their own rows.
- `curl -c` without `-b` overwrites a cookie jar (caused a false alarm once).

## Phase 7 eval ideas already noted
- Reply text that names a blocked dish as a pick (guard checks IDs, not text).
- The model offering to "include non-vegetarian dishes" to a vegetarian.
- Extraction precision ("my friend is vegan"), corrections, isolation.

## Where things are
Plan: `docs/plan.md`. Architecture: `docs/architecture.md`. Decisions:
`docs/decisions/` (0001 to 0017). Requirements trace: `docs/requirements.md`.
Each backend package and the frontend has a README.
