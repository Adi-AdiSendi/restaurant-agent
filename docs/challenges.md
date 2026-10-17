# Challenges we faced

The problems that cost real time, what we did about each, and what we took
away. Most are from deployment (phase 6) and evaluation (phase 7). Each one
links to the code or decision record where the fix lives.

## 1. Moving from Railway to Netlify
**What happened.** The plan was one Railway service (FastAPI serving the built
frontend) plus Railway Postgres ([ADR 0006](decisions/0006-deploy-railway.md)).
Railway did not accept our credit card, so we could not use it. We moved the
deployment to Netlify.

**Why it was not a simple swap.** Netlify hosts static sites and serverless
functions in JavaScript, TypeScript or Go. It cannot run our Python FastAPI
backend. We weighed three ways forward:
- **Rewrite the backend as TypeScript Netlify Functions.** One host, but it
  meant redoing the agent loop, memory, the allergen guard, login and about
  230 tests (6 to 10 hours). It would also throw away the tests that prove
  the safety guarantees. Rejected.
- **A paid always-on host for the backend** (Render Starter, Fly.io).
  Rejected: paying for a prototype brings no real value.
- **Free hosting, split in two (chosen).**
  - Netlify serves the React build and is the only URL users see.
  - Netlify proxies every `/api/*` request to the unchanged backend on
    Render's free plan, which runs natively with `uv` (no Docker any more).
  - The database is Netlify DB (Postgres).
  - So the backend now connects to Netlify's database, and the browser
    reaches the backend only through Netlify.

**The decision record:** [ADR 0017](decisions/0017-deploy-netlify-with-api-proxy.md),
which supersedes 0006. The split created most of the challenges below.

## 2. A hard 26-second limit on every request
Netlify's proxy gives up after 26 seconds, and that limit cannot be changed.
One chat turn makes several model calls. We added a 22-second server deadline:
a slower turn is rolled back and returns a clear "took too long, please try
again" instead of a proxy error page
(`backend/app/agent/chat_turn.py`). Measured on the live site: median 5.2 s,
p95 7.5 s.

## 3. The free backend falls asleep
Render's free plan sleeps after 15 idle minutes and takes about a minute to
wake. That is longer than the proxy waits.
- **Keep it awake.** A Netlify scheduled function calls `/api/health` every
  10 minutes (`frontend/netlify/functions/keep-awake.mts`). The health check
  never touches the database, so the database can still sleep.
- **Handle the case where it sleeps anyway.** The UI shows "Starting the
  server" and retries until the backend answers
  (`frontend/src/features/startup/`).
- **A gap the review found.** The first version showed a blank page for up to
  26 s before that message appeared. Now it appears after 1 s, and each check
  gives up after 5 s and retries.

## 4. Would the login cookie survive the proxy?
Everything depended on the session cookie working through Netlify's proxy.
If it did not, logins would silently fail. We tested it first, before
building anything else. It works: the cookie is set on the Netlify domain
(first-party, `HttpOnly`, `Secure`, `SameSite=Lax`) and comes back on the
next request, so no CORS or cross-site cookie setup was needed.

## 5. Netlify DB was new and under-documented
Netlify DB had just become Netlify's own product. Its docs did not say whether
a server outside Netlify could connect, or which connection string to use.
We tested it from outside:
- It accepts outside connections over TLS 1.3 and refuses unencrypted ones.
- It gives a direct connection, not a pooler. That matters: our database
  driver (asyncpg) breaks behind a transaction pooler.
- Its connection string uses `sslmode=`, which asyncpg rejects, so the
  settings now translate it (`backend/app/config.py`).
- It runs in `us-east-2`. We had put the backend in Frankfurt, so every
  database query would have crossed the Atlantic. We moved the backend to
  Render's Ohio region.

## 6. A database that must be allowed to sleep
Netlify DB Free sleeps after 5 idle minutes and allows 48 compute hours per
billing period. A normal connection pool keeps connections open, which could
keep the database awake around the clock and use up the month's hours in about
two days. In production the app now opens one connection per request and
closes it (`backend/app/db/engine.py`).

## 7. Spaces in pasted secrets
Two failures, one cause:
- The database URL had two spaces in front of it, so it was not recognised
  and the app tried a database driver we do not install.
- On the live site, every chat turn returned "The assistant is unavailable",
  while login and the database worked. The OpenAI key pasted into the hosting
  dashboard carried surrounding spaces.

Fix: every setting is stripped of surrounding whitespace on load. The lesson:
values pasted into dashboards are untrusted input too.

## 8. Dashboard surprises
- **A new Netlify site was private by default.** Visitors got a Netlify login
  page instead of the app. It had to be made public.
- **Two names for one project.** The project was renamed from
  `jovial-gelato-6307c0` to `restaurant-agent`, and testing the old name
  looked like a failed deploy.
- **"Canceled" Netlify builds.** These appear when only backend files change.
  That is normal: Netlify skips a build when the frontend did not change.
- **The Render URL is derived from the service name.** If the name had been
  taken, the proxy would have sent users' logins to someone else's server. We
  confirmed the URL belongs to us, by logging in as a demo user, before
  pointing Netlify at it.

## 9. Our own mistakes
- **A seed script ran against the wrong database.** A failed command earlier
  in a chain meant the database address was never switched, so the
  demo-user reset hit the local database instead of Netlify DB. It deleted
  the local demo users' chat history. Since then, every script that writes to
  a hosted database first checks the host and stops if it is wrong.
- **Shell quirks.** Inline scripts containing an apostrophe fail in this
  environment's shell, and `\n` escapes became real line breaks in generated
  test files. We now write such scripts to files.

## 10. The evals were too easy at first
The first eval run passed 35 of 36 cases. That is good news, but it shows
little. We added 6 harder cases aimed at weak spots we had seen live. They are
marked `added_after_baseline` and got their own run before any fix, so the
report cannot pass them off as part of the original set.

## 11. A fix that made things worse, and passed every test
The evals found that memory changed silently: after "I'm vegetarian now, not
vegan", the memory and the cards were right, but the reply never said so.
- **First fix:** tell the model what changed and ask it to confirm "in one
  short sentence". Every graded check passed.
- **What the code review found:** whole replies had become short. Replies
  that left the user with nothing to do (no dish, no question) rose from 18
  to 43 out of 159. "What are you in the mood for?" disappeared.
- **Third fix:** confirm in one sentence, then answer as usual. That brought
  those replies down to 11, better than where we started.

The lesson: graders only see what they check. We now report that number in
every eval run. Details: [eval-report.md](eval-report.md).

## 12. Slow eval runs
Each eval case re-seeded the menu inside its own long transaction, so cases
meant to run 4 at a time waited on each other's database locks and ran one at
a time. Seeding once per run cut a full run from about 14 minutes to 4.

## Earlier phases (0 to 5)
- **Reasoning model between tool calls.** gpt-6-luna is a reasoning model.
  Its reasoning must be sent back between tool rounds
  (`include=["reasoning.encrypted_content"]`, `store=False`), or it loses track.
- **Memory edits must hit the right fact.** A correction could target the wrong
  row; changes are now checked against their target
  ([ADR 0016](decisions/0016-removed-status-and-target-checks.md)).
- **Races.** Two quick messages from one user could race on the same
  preferences. Each turn now locks that user's row.
- **Blocking work.** PIN hashing (argon2) was moved off the event loop.
- **Windows tooling.** pytest needs a project-local temp folder. The current
  Starlette test client needs `httpx2`. Tests that share the dev database with
  real-model runs must count only their own rows.
