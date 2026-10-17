---
paths:
  - "frontend/**"
---
# Frontend rules

## Scope
A simple, clear chat UI. The brief says a production-grade frontend is not
expected. Spend effort on clarity, not features.

## Layout
- `src/features/<feature>/` holds one feature's components, hooks and types
  (`features/chat/`, `features/login/`).
- `src/api/` is the only place that calls the backend. Components never call `fetch`.
- `src/components/` is for UI pieces used by two or more features. Do not
  create it until a second feature needs the component.

## Conventions
- TypeScript strict. No `any`; no `@ts-ignore` without a comment explaining why.
- Function components and hooks only. Local state with `useState`/`useReducer`;
  no global state library.
- Types for API payloads mirror the backend Pydantic models. Keep them in
  `src/api/types.ts`.
- One component per file, named like the file (`MessageList.tsx`).
- Styling: plain CSS modules. No UI framework unless an ADR adds one.

## Grounding in the UI
- Recommended items render as cards from the item data the backend returns
  (name, price, spice, diet flags, allergens). Never parse dish details out of
  the assistant's text.
- Show allergens on every card. Safety information must be visible, not hidden
  behind a click.

## Behaviour
- Show a loading state while the assistant is thinking and a clear message on
  errors, with a retry option.
- The user can start a new conversation and log out. Both are needed to demo
  memory across independent conversations.
- Keep the API base URL relative (`/api`): FastAPI serves the build locally,
  and Netlify proxies `/api` when deployed.

## Testing
- Vitest + React Testing Library for components with logic.
- Do not test styling or third-party behaviour.
