# 0017: Deploy on Netlify, with the API behind a proxy

- Status: Proposed (supersedes [0006](0006-deploy-railway.md) when accepted)
- Date: 2026-10-17

## Context
The user chose Netlify instead of Railway for the deployed app. The backend
is a long-running FastAPI service with async Postgres, and one chat turn makes
several OpenAI calls (often 5 to 15 s). Netlify Functions run JS, TS or Go,
time out after 10 s by default (26 s on paid plans), and cannot host the
existing Python service without a rewrite.

## Decision
- Netlify serves the React build and is the public URL.
- A Netlify proxy rule (`/api/*` to the backend, status 200) forwards API calls
  to the unchanged FastAPI Docker image on an always-on container host. The
  browser only ever talks to the Netlify domain, so the session cookie stays
  first-party and no CORS setup is needed.
- Postgres on Netlify DB (Neon), using the direct connection string.
- A server-side turn deadline keeps every chat turn under the 26 s proxy timeout.

## Alternatives considered
- Rewrite the backend as Netlify Functions in TypeScript: throws away the
  tested Python stack (ADR 0003) and still hits the function time limit.
- Browser calls the backend host directly: needs CORS and cross-site cookies
  (`SameSite=None`), which browsers increasingly block.
- Keep Railway (ADR 0006): rejected by the user.

## Consequences
- Two hosts to run (Netlify and the backend host) instead of one.
- The 26 s proxy limit becomes a hard latency budget for a chat turn.
- Must verify that the proxy passes `Set-Cookie` through; it is the first
  step of phase 6.
