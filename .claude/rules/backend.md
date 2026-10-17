---
paths:
  - "backend/**"
---
# Backend rules

## Layout
- `app/api/` holds FastAPI routes only: parse request, call one function, return.
  No business logic or SQL in routes.
- `app/agent/` owns the LLM loop and prompts. It is the only module that calls OpenAI
  for chat; `app/memory/extract.py` is the only other caller.
- `app/tools/` defines tools the model can call. Each tool is one file:
  schema, description, handler.
- Tests live in `backend/tests/` mirroring `app/` (`tests/memory/test_supersede.py`).

## Python conventions
- Full type hints; pyright strict must pass. No `Any` unless justified in a comment.
- Pydantic models at every boundary: API bodies, tool args, tool results, LLM output.
- Async all the way down. Use one `AsyncSession` per request via a dependency.
- Settings only through `app/config.py` (pydantic-settings). Never read `os.environ` elsewhere.
- Raise domain exceptions in lower layers; translate to HTTP errors in `app/api/`.
- Log with the standard `logging` module, structured key=value fields.
  Never log PINs, session tokens or API keys.

## Database
- Every schema change is an Alembic migration. Never edit a migration after it is merged.
- Allergens use the fixed vocabulary in `app/menu/allergens.py`. User wording
  ("lactose intolerant") is mapped to it at extraction time, never matched as free text.
- Prices are `NUMERIC(8,2)` in SAR. Never floats.

## LLM and agent loop
- Use the OpenAI Responses API. Model ID from settings, never hard-coded.
- The loop ends when the model returns no tool calls. Do not add content-based
  stop conditions. Keep a max-iteration guard (default 5) that fails loudly.
- Append complete tool results to context. Do not summarize or trim fields the
  model may need (allergens, price, spice, diet flags).
- The user profile block goes at the top of the context on every turn, not
  inside the history. Hard constraints are never summarized away.
- The final answer is structured: `{reply: str, recommended_item_ids: list[int]}`.
  An item is recommended by ID; options are checked by the guard, never trusted.
- On schema validation failure, retry once with only the failed fields and the
  validation error. Then fail with a clear error.

## Tool design
- Tools have distinct purposes. Each description states: what it does, input
  format, an example, and what it must NOT be used for.
- Tools never accept `user_id`, a conversation or a restaurant. Handlers take
  `(arguments, context)`; `ToolContext` is built by the server (ADR 0020).
- `search_menu` always applies the user's hard constraints server-side, whatever
  arguments the model sends.
- No results is a success with an empty list, never an error.
- Errors return `{error_category, retryable, message}`. Validation errors are
  not retryable; timeouts and connection errors are.

## Testing
- Unit tests never call the real LLM. Inject a fake client.
- `app/safety/` and `app/memory/` need tests for every branch; they carry the
  hard guarantees.
- Use a real Postgres (docker compose) for DB tests, not SQLite.
