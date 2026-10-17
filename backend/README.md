# backend

FastAPI app that serves the API under `/api` and the built frontend at `/`.

- Entry point: `app/main.py` (`create_app`).
- Settings: `app/config.py`, read from env or the repo-root `.env`.
- Layers, top to bottom: `api -> agent -> tools | memory | safety -> menu | users -> db -> config`.
  Lower layers never import higher ones; `uv run lint-imports` enforces it.
- Migrations: `migrations/` (Alembic, async). Tests: `tests/`, mirroring `app/`.
- New ORM models live in their feature folder and must be imported in
  `migrations/env.py`, or autogenerate will miss (or try to drop) their tables.
- Menu seed: `data/menu.json`, loaded by `scripts/seed_menu.py` (upsert by name, delete dishes no longer listed).
- DB tests need `docker compose up -d db` and `alembic upgrade head`; each test
  runs in a transaction that is rolled back.

## Run
```
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed_menu
uv run uvicorn app.main:app --reload
```

## Checks
```
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest
```
