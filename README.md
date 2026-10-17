# Restaurant Ordering Assistant

An AI assistant that helps people choose from a restaurant menu and remembers
them across conversations. Built for an AI Engineer take-home. Work in progress;
see `docs/plan.md` for the current phase.

## Run locally
Needs Docker, uv and Node 22+.
```
cp .env.example .env            # then fill in OPENAI_API_KEY and SESSION_SECRET
docker compose up -d db
# terminal 1
cd backend && uv sync && uv run alembic upgrade head && uv run python -m scripts.seed_menu && uv run uvicorn app.main:app --reload
# terminal 2
cd frontend && npm install && npm run dev
```

## Docs
- Architecture: `docs/architecture.md`
- Decisions: `docs/decisions/`
- Requirements traceability: `docs/requirements.md`

## Known limitations
- Reloading the page starts a new conversation; past conversations are kept
  in the database but not listed in the UI. Memory carries over either way.
- Identity is a username and a 4-digit PIN (ADR 0013), with no lockout after
  wrong guesses. Fine for a demo, not for production.
- Sessions are stateless signed cookies: logout clears the browser's copy, but
  a copied cookie stays valid for 30 days unless `SESSION_SECRET` changes.
- The safety guard checks recommended item IDs, not the reply text. The model
  may describe an unsuitable dish (ADR 0009, with a warning), and in rare cases
  the text could still suggest one without a card. Cards are always safe.
- A chat turn holds one database transaction open across its LLM calls (so a
  failure rolls back everything). This limits concurrent chats to the pool
  size, about 15; fine for a demo.
- The Foodics name, logo and colours are used for this prototype only. The
  restaurant is fictional.
