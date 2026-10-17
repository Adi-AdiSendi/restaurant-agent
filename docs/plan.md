# Build plan

Budget: about 10 to 12 focused hours inside the 72-hour window.
Rule: the baseline must work end to end (deployed) before Part 2 starts.
Every phase ends with all checks green and a `code-reviewer` pass.

**Current phase: 8** (video deferred; see handoff)

## Inputs
- Menu concept: international casual (burgers, bowls, pasta, desserts), prices in SAR.
- UI brand: Foodics colours, font and logo, with a fictional restaurant name and
  "Powered by Foodics" (ADR 0015).
- Reference app: `D:\Programing\APP\Claude\HR Recruitment` (same stack, on Railway).
  Reuse its Dockerfile, start script, SPA static mount, Railway URL rewrite,
  Responses API wrapper ideas, fake OpenAI client in tests, argon2 settings and CI shape.
  Do not reuse its sync DB layer, mypy setup, Railway IaC, DB sessions, RLS or CSRF.
- Lessons from it: Railway pre-deploy is one `&&`-joined string; deploy from git,
  never from a dirty tree; keep files UTF-8; on Windows run pytest with a local `--basetemp`.

## Phase 0: Scaffold (about 1 h)
- `git init`, private GitHub repo.
- Backend: uv project, FastAPI app with `/api/health`, SPA static mount,
  pydantic-settings config (rewrites `postgres://` to `postgresql+asyncpg://`),
  async engine and session dependency, ruff, pyright strict, pytest, import-linter.
- Alembic with the async env template.
- Frontend: Vite React TS strict, ESLint, Prettier, Vitest, `/api` dev proxy.
- `docker-compose.yml` with Postgres 16, root `Dockerfile` (3-stage), `railway.toml`.
- CI (GitHub Actions): Postgres service, lint, types, tests, line limits,
  import-linter, secret scan, Docker build. Pre-commit with the same checks.
- Done when: all local checks are green and the Docker image builds and serves
  `/api/health`. CI runs once the repo is pushed (no commits yet, by choice).
- Status: done 2026-10-17.

## Phase 1: Menu and database (about 1 h)
- Allergen vocabulary, `menu_items` model and migration.
- `data/menu.json`: about 16 items in 4 categories (Starters, Burgers and Mains,
  Bowls and Pasta, Desserts and Drinks), SAR 12 to 85, veg, vegan and non-veg,
  spice 0 to 3. Designed conflicts: pesto pasta with pine nuts vs tomato pasta,
  spicy veg bowl vs mild veg bowl, two burgers at different prices, a
  "may contain" dessert.
- Idempotent seed script; menu query functions with filters.
- Done when: seed runs twice cleanly, menu tests cover M1 to M5.
- Status: done 2026-10-17. The seed also deletes dishes the file no longer lists.

## Phase 2: Agent and tools (about 2 h)
- `search_menu` and `get_item` tools following the tool design rules. The
  `search_menu` description points the model to the `category`, `vegan` and
  `vegetarian` filters rather than free text for those.
- Thin Responses API client (injectable), system prompt, structured final
  answer, tool loop with max 5 iterations, one retry on bad schema.
- `POST /api/chat` without memory yet (anonymous).
- Done when: a scripted conversation returns grounded recommendations.
- Status: done 2026-10-17. Also: cards only for IDs a tool returned this
  turn; reasoning items replayed between tool rounds (gpt-6-luna is a
  reasoning model); every OpenAI API error maps to 503.
- Manual run on gpt-6-luna, one message each, no memory yet:
  | Request | Cards |
  |---|---|
  | vegan, not spicy, under 45 SAR | Mediterranean Veggie Bowl 39, Mango Sorbet 22 |
  | tree nut allergy, dessert | Mango Sorbet (skipped the may-contain lava cake) |
  | best burger, hates mustard | Plant-Based Burger (both beef burgers have mustard) |
  | turn 2 of the first: sesame allergy, a main | none; said nothing fits, offered to relax a need |

## Phase 3: Users and memory (about 2 h)
- Username + PIN login, argon2 hash, signed session cookie. Accept ADR 0013.
- `conversations`, `messages`, `preferences` models and migrations.
- Extraction pass, supersession, profile block in context.
- Done when: a fact from conversation 1 changes recommendations in
  conversation 2, a correction replaces the old fact, two users stay isolated.
- Status: done 2026-10-17. Also `GET /api/preferences` (with history) for a
  "what I remember" panel; IDs recommended earlier in a conversation stay valid.
  Review fixes: memory changes must match their target (ADR 0016), per-user
  row lock per turn, scoped history reads, argon2 off the event loop.
- Manual run on gpt-6-luna (user `demo_alice`, then `demo_bob`):
  | Step | Result |
  |---|---|
  | conv 1: "allergic to peanuts, love really spicy food" | stored allergy peanut, spice hot; wings + Nashville chicken |
  | conv 2 (new): "What should I get today?" | Nashville chicken + wings again, from memory alone |
  | conv 2: "gone vegetarian since last time" | stored diet vegetarian; Penne Arrabbiata + Edamame (skipped the peanut Thai bowl) |
  | conv 3: "mild spice at most from now on, under 45 SAR" | spice hot superseded by mild; Mediterranean Veggie Bowl (spice 0, 39) |
  | demo_bob | empty profile; 404 on alice's conversation |

## Phase 4: Safety guard (about 1 h)
- Hard constraints injected into `search_menu`; post-check on final IDs;
  one corrective retry whenever a card is blocked; may-contain warning flag.
- The post-check must also cover IDs carried over from earlier in the
  conversation. Test: item recommended, allergy added later, card dropped.
- Status: done 2026-10-17. Exhaustive test: a fake model that recommends all
  18 items, for each of the 10 allergens and both diets, never gets a
  violating card. Cards carry `may_contain_warnings`.
- Manual run on gpt-6-luna as `demo_alice` (peanut, vegetarian, mild):
  | Request | Result |
  |---|---|
  | "Can I get the Thai Peanut Noodle Bowl?" | no card; explained the peanut allergy, offered an alternative |
  | "Show me your chicken dishes" | no card; said none fit the vegetarian diet |
  | "Something sweet and chocolatey" | Chocolate Lava Cake, with a may-contain tree nut note |
- Eval idea for phase 7: reply text that names a blocked dish as a pick.
- Eval idea for phase 7: the model offered "include non-vegetarian dishes?";
  the guard would still block them unless the diet is actually changed.
- Done when: unit tests prove no path returns a violating item.

## Phase 5: Frontend (about 1.5 h)
- Foodics theme tokens (ADR 0015), IBM Plex Sans, local copy of the logo.
- Login, chat window, item cards with allergens always visible, new
  conversation, logout. Header: logo, restaurant name, "Powered by Foodics".
- Done when: the full baseline works in the browser locally.
- Status: done 2026-10-17. Also a "What I remember about you" panel
  (active facts, hard ones marked "always enforced", old ones struck through)
  and suggestion chips. A page reload starts a new conversation.

## Phase 6: Deploy for free (about 1.5 h) - replanned 2026-10-17
Railway is dropped, and so is paid hosting (ADR 0017, supersedes 0006).
Netlify Functions cannot run Python (JS, TS, Go; 60 s), and a TypeScript
rewrite was rejected on cost and risk, so:
- **Netlify** serves the React build and is the only URL reviewers use.
  `netlify.toml` proxies `/api/*` (status 200) to the backend, so the cookie
  stays first-party. The proxy stops at a fixed 26 s.
- **Render free** runs the unchanged backend, native Python with uv
  (`render.yaml`). No Docker online; the build migrates and seeds.
- **Netlify DB** (Postgres, TLS). Fallback: Neon free.
- **Sleep**: Render free sleeps after 15 idle minutes (about 1 min to wake).
  A Netlify scheduled function pings `/api/health` every 10 minutes; the UI
  shows "Starting the server" and retries for up to 2 minutes.
- **Git**: commits and a private GitHub repo; both hosts deploy on push.
- Steps:
  1. Baseline commit, private repo, CI green. Done.
  2. `sslmode` to `ssl` in hosted DB URLs. Done.
  3. 22 s turn deadline with a clear 504; OpenAI timeout 15 s, one retry. Done.
  4. `render.yaml`, `start.sh`; Dockerfile, `railway.toml`, CI container job removed. Done.
  5. `seed_demo_users.py`: `demo_alice` / `demo_bob`, reset each deploy. Done.
  6. `netlify.toml` with the proxy and SPA fallback. Done.
  7. Startup gate in the UI (`features/startup/`). Done.
  8. Keep-awake scheduled function. Done.
  9. Spike on the live setup. Done: Netlify DB is reachable from outside
     Netlify over TLS 1.3 (plain text refused); the string is direct, not a
     pooler; Postgres 18.6 in us-east-2, so Render runs in Ohio; migrations
     and seeds ran on it. Render builds with Python 3.12 and uv and answers at
     `restaurant-agent-api.onrender.com`. Through `restaurant-agent.netlify.app`:
     `Set-Cookie` arrives first-party (`HttpOnly; Secure; SameSite=Lax`) and
     comes back; SPA deep links work. Found live: values pasted into Render
     carried spaces, which broke the OpenAI key (every turn 503); settings now
     strip whitespace.
  11. Close-out checks, 2026-10-17 (scripts in the session scratchpad, not committed):
      - **Keep-awake did not work at first.** After 16.5 idle minutes,
        health got a proxy 504 after 28.6 s: Render was asleep, although
        Netlify's metrics showed the function running every 10 minutes. It
        called the site's own `/api` proxy. It now calls Render directly
        (a test keeps the URL in sync with `netlify.toml`). After 20 idle
        minutes: health 200 in 1.29 s.
      - **Cold start, measured** with the ping paused for 20 minutes
        (commits 7bdf160 and its revert), using the UI's own loop (5 s
        abort, retry every 3 s): 4 timed-out attempts, then
        `{"status": "ok"}` at 33.5 s. Then, with Render and the DB both
        just woken: login 1.6 s, first chat turn 7.7 s with two cards.
        The UI gives up at 120 s, so there is plenty of margin.
      - **Netlify DB sleeps when idle.** Three fresh connections in a row,
        timed. After 20+ idle minutes the first took 2.13 s and the next
        two about 1.1 s; a warm control straight after had a fast first
        connection (1.11 s). After 7.5 idle minutes, 1.94 s against 1.15 s.
        Waking costs about 1 s, and nothing in the app keeps it awake.
- Status: done 2026-10-17.
  10. Docs and ADRs. Done. Then `code-reviewer`.
- Done when: the baseline works on the Netlify URL from a fresh browser
  (login, memory across chats, a correction, isolation, an allergen block),
  10 real turns stay under 22 s (record p95 here), and the DB sleeps when idle.
- Live run 2026-10-17, 10 real turns through the Netlify proxy on gpt-6-luna:
  min 4.6 s, median 5.2 s, **p95 7.5 s**, max 7.5 s. All passed:
  | Check | Result |
  |---|---|
  | demo_alice "What should I get today?" | mild vegetarian picks from memory |
  | "Can I get the Thai Peanut Noodle Bowl?" | refused, peanut allergy, no card |
  | "Show me your chicken dishes" | none, vegetarian |
  | "Something sweet and chocolatey" | lava cake with the may-contain tree nut note |
  | demo_bob vegan, no spice; new chat | memory carried over |
  | "not vegan anymore, just vegetarian" | vegan superseded, vegetarian active |
  | bob on alice's conversation | 404; alice's memory unchanged |
- Eval idea for phase 7: bob ("no spice", soft) asked for a burger and was
  told none fit; the Plant-Based Burger (spice 1) was not even offered.

## Phase 7: Part 2, reliability and evals (about 2.5 h)
- Eval cases per category, deterministic graders, runner, committed results.
- Run, find failures, fix the system, run again. Keep the before/after.
- `docs/eval-report.md` with per-category results and explained failures.
  Accept ADR 0014.
- Done when: the report shows per-category results and at least one real
  improvement measured before and after.
- Status: done 2026-10-17. 42 cases (36 + 6 added after the first baseline),
  3 runs each. preference_update went 4/6 to 6/6 through fixes to a
  memory-change note; the review found the first two shortened replies, and
  a third fix took dead ends from 43 back to 11 (baseline 18). The other six
  categories stayed at 100%. ADR 0014 accepted. Report: `docs/eval-report.md`.

## Phase 8: Submission (about 1.5 h)
- README: local setup, architecture, key decisions (link ADRs), setup
  requirements, known limitations, demo accounts.
- Video 8 to 12 minutes following brief section 6.3.
- Drive folder; check every link from a logged-out browser.

## Out of scope (deliberately)
Placing real orders or payments, multiple restaurants, voice, Arabic UI,
dark theme, real authentication, admin menu editing. Each is noted in README
limitations.
