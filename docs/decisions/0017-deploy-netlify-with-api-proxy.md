# 0017: Deploy on Netlify, with the API on Render free behind a proxy

- Status: Accepted (supersedes [0006](0006-deploy-railway.md))
- Date: 2026-10-17

## Context
The user chose Netlify instead of Railway, and no paid hosting for a
prototype. The backend is a long-running FastAPI service with async Postgres;
one chat turn makes several OpenAI calls (often 5 to 15 s). Netlify Functions
run JS, TS or Go only (60 s limit), so hosting the backend there means a full
rewrite of a tested Python stack (ADR 0003).

## Decision
- **Netlify** serves the React build and is the public URL.
- **Proxy**: `/api/*` is rewritten (status 200) to the backend. The browser
  only talks to the Netlify domain, so the session cookie stays first-party
  and no CORS setup is needed.
- **Backend**: the unchanged FastAPI app on **Render free**, native Python
  runtime with uv (`render.yaml`). No Docker image; Docker stays only for the
  local Postgres. Migrations and seeds run in the build, once per deploy.
- **Database**: Netlify DB (Postgres), reached from Render with TLS.
- **Latency budget**: the proxy gives up after a fixed 26 s, so a chat turn
  has a 22 s server deadline and ends with a clear 504.
- **Sleep**: Render free sleeps after 15 idle minutes and takes about a
  minute to wake. A Netlify scheduled function pings `/api/health` every 10
  minutes, and the UI shows "Starting the server" and retries if it is asleep.

## Alternatives considered
- Rewrite the backend as Netlify Functions in TypeScript: one host and no
  cold start, but redoes phases 1 to 4 and their tests. Rejected on cost and risk.
- Paid always-on host (Render Starter, Fly.io): no cold start. Rejected by the
  user: money for a prototype.
- Render free alone, without Netlify: simplest, but the user wants Netlify.
- Browser calls the backend directly: needs CORS and cross-site cookies
  (`SameSite=None`), which browsers increasingly block.
- Google Cloud Run free tier: fast cold starts, but needs a billing account.

## Consequences
- Two hosts (Netlify and Render) and one database to run.
- 22 s is a hard limit for a chat turn.
- A cold start after a missed ping costs up to a minute on first load.
- Free-tier caps: 750 Render hours a month (one service fits), and Netlify DB
  Free sleeps after 5 idle minutes with 48 compute hours per billing period.
- The CI container build is gone, since nothing ships a container.
