# 0006: Deploy on Railway as one service

- Status: Accepted
- Date: 2026-10-17

## Decision
Deploy on Railway: one app service (FastAPI serving the built frontend) plus
Railway Postgres. Keep the service always-on during the evaluation window.

## Why
- Git-based deploys and managed Postgres in one project, set up in minutes.
- Railway's MCP server lets Claude Code deploy and read logs during
  development. This is a workflow benefit, not part of the app.
- Serverless (app sleeping) suits a prototype that is rarely used.

## Why always-on during evaluation
- The brief requires the app to remain available throughout evaluation.
- Railway only sleeps a service after 10 minutes with no outbound traffic, and
  an open database connection pool can stop it from sleeping at all.
- Slept services are de-prioritized and can, in rare cases, need a rebuild.
  A reviewer hitting a slow or dead first load is a real risk.
- After evaluation, enabling Serverless is the cost strategy. Noted in README.

## Consequences
- A few dollars of hosting cost during evaluation.
- Single region, single instance. Fine for a demo; listed as a limitation.
