# Restaurant Ordering Assistant

AI assistant that helps users choose from a restaurant menu and remembers them
across conversations. Built for an AI Engineer take-home: reviewers reward
judgment over complexity, working software, and evidence over claims.

## Read before working
These are plain paths, not imports. Open them when the task needs them.
- `docs/plan.md`: phases and the current phase. Work only on the current phase.
- `docs/architecture.md`: folder map, request flow, data model.
- `docs/requirements.md`: brief requirements and where each is implemented.
- `docs/decisions/`: accepted decisions. Do not contradict one silently;
  propose a new ADR that supersedes it.

## Stack
v2 (phases 9 to 18, ADRs 0018 to 0023) adds restaurants with options, a
cart and orders, React Router, voice input and CRMs. Update these lines as
each lands. Landed: six restaurants with options (phase 10); tools take a
server-built `ToolContext` (ADR 0020); cart, checkout and orders in
`app/orders/` and React Router pages (phase 11).
- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async) + asyncpg, Alembic
- Database: PostgreSQL 16
- LLM: OpenAI GPT-6 Luna via the Responses API (model ID from `OPENAI_MODEL`)
- Frontend: React + Vite + TypeScript (strict), static build (Netlify; FastAPI locally)
- Tooling: uv, ruff, pyright (strict), pytest, ESLint, Prettier
- Deploy (ADR 0017): Netlify serves the UI and proxies `/api/*` to FastAPI on
  Render free (native uv, `render.yaml`); Netlify DB. Docker is for the local DB only.

## Commands
- Local DB: `docker compose up -d db`
- Backend: `cd backend && uv run uvicorn app.main:app --reload`
- Migrate: `cd backend && uv run alembic upgrade head`
- Seed menu: `cd backend && uv run python -m scripts.seed_menu`
- Frontend: `cd frontend && npm run dev`
- Backend checks: `cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest`
- Frontend checks: `cd frontend && npm run lint && npm run typecheck && npm test`
- Line limits: `python scripts/check_line_limits.py`
- Evals: `cd backend && uv run python -m evals.run`

## Hard rules (non-negotiable)
1. **100-line limit** for every source file, CLAUDE.md, rule and agent file.
   Tests may reach 150. Exempt: migrations, lockfiles, seed data, generated code.
   If a file grows past the limit, split it by responsibility, not arbitrarily.
2. **Allergens and diet are enforced in code**, never only in the prompt.
   Hard constraints are injected into menu queries server-side and every
   recommended item passes `app/safety/` before it reaches the user.
3. **Grounding**: the model recommends items by ID only. The server validates
   every ID and the UI renders name, price, ingredients and allergens from the
   database, never from model text.
4. **User isolation**: `user_id` comes from the session, never from model or
   tool arguments. Every memory query is scoped by it.
5. **No secrets in the repo.** Settings come from env via `app/config.py`;
   keep `.env.example` updated when adding a setting.
6. **One-way dependencies**: `api -> agent -> tools | memory | safety -> orders -> menu | users -> db`.
   Lower layers never import higher ones.

## How we work
- Spec first. For a new module, use plan mode and agree the design before
  writing code. For a well-scoped function, implement directly.
- One function or feature at a time, with its tests in the same change.
- Run the relevant checks before saying a task is done. Report failures as
  they are; do not weaken a test to make it pass.
- After a feature, ask the `code-reviewer` agent to review it in its own context.
- New dependency: say why in the commit message. Significant ones need an ADR.
- No commented-out code, no TODO comments. Known gaps go in the README
  "Known limitations" section.
- Keep each folder's README accurate when its contents change.
- Prefer the simplest design that meets the requirement. No speculative
  abstractions (repository layers, plugin systems, extra services).

## Writing style
- Docs and user-facing copy: short, plain English, no em dashes.
- Commit messages: imperative mood, one logical change per commit.
- Names say what things do: `memory/supersede.py`, not `memory/utils.py`.
  No `utils/`, `helpers/` or `common/` folders.
