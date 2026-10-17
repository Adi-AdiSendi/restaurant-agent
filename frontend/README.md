# frontend

React + Vite + strict TypeScript chat UI with the Foodics brand (ADR 0015).
Built to `dist/`. Locally FastAPI serves it from the same origin; deployed,
Netlify serves it and proxies `/api` to the backend (`../netlify.toml`).

- Entry point: `src/main.tsx`; `src/App.tsx` waits for the server, checks the
  session and shows login or chat.
- `src/api/`: the only code that calls the backend (`client.ts`), and payload
  types that mirror the Pydantic models (`types.ts`).
- `src/features/startup/`: polls `/api/health` while the free backend wakes
  up ("Starting the server"), gives up after 2 minutes with a retry button.
- `src/features/login/`: username + 4-digit PIN.
- `src/features/chat/`: header (logo, "Corner Table", "Powered by Foodics",
  New chat, Log out), messages, item cards, composer, suggestions. State is a
  pure reducer (`chatReducer.ts`) driven by `useChat.ts`. Cards render only
  from backend item data; allergens are always visible and may-contain
  warnings are highlighted.
- `src/features/memory/`: "What I remember about you", from `/api/preferences`,
  refreshed after each reply. Old facts are struck through. `ChatPage` hosts
  it next to the chat; that is the only import between features.
- `netlify/functions/keep-awake.mts`: Netlify scheduled function that pings
  `/api/health` every 10 minutes so the free backend stays awake.
- `src/theme.css`: brand tokens as CSS variables. Components use CSS modules.
- Dev server proxies `/api` to `http://localhost:8000`.

## Run

```
npm install
npm run dev
```

## Checks

```
npm run lint && npm run typecheck && npm test
```
