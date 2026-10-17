# 0004: PostgreSQL for menu, users and memory

- Status: Accepted
- Date: 2026-10-17

## Decision
PostgreSQL 16 for all persistent data. Railway Postgres in production,
Docker Compose locally. Schema managed with Alembic.

## Why
- The menu is relational and constraint-heavy. SQL filters on allergens, diet,
  price and spice give hard guarantees before the model sees any item.
- Preference updates must replace old facts atomically. Transactions make
  supersession safe.
- Every memory query is scoped by `user_id`, which makes isolation simple to
  prove.
- Array columns fit allergens and ingredients. JSONB and pgvector are there if
  a later phase needs them, without adding a new database.

## Alternatives considered
- JSON file: fine for the menu alone, but not for per-user memory.
- SQLite: simpler, but Railway's filesystem is not durable across redeploys,
  so memory would be lost.
- A vector database: semantic recall is not needed for a small set of typed
  preferences.

## Consequences
- Tests need a real Postgres via Docker Compose.
