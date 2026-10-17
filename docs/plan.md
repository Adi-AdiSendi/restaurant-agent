# Build plan

Budget: about 10 to 12 focused hours inside the 72-hour window.
Rule: the baseline must work end to end (deployed) before Part 2 starts.
Every phase ends with all checks green and a `code-reviewer` pass.

**Current phase: 6**

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

## Phase 6: Deploy on Netlify (about 1.5 h) - replanned 2026-10-17
Railway is dropped; the user chose Netlify. Proposed ADR 0017 supersedes ADR
0006 once accepted. Netlify cannot run the FastAPI server (functions are
JS/TS/Go, 10 s default and 26 s max on paid plans), so:
- **Netlify** hosts the React build and is the only URL reviewers use.
  `netlify.toml`: base `frontend`, command `npm ci && npm run build`, publish
  `dist`; redirect `/api/*` to `https://<backend-host>/api/:splat` with status
  200 (proxy, so the browser stays on the Netlify domain and the session
  cookie stays first-party, same as today); then `/*` to `/index.html` 200.
- **Backend**: the existing Docker image on an always-on container host
  (decision for the user: recommended Fly.io or Render paid; Railway for the
  backend only is also possible). Not exposed to reviewers directly.
- **Database**: Netlify DB (Postgres by Neon), to keep the stack on Netlify,
  or Neon directly. Use the direct (unpooled) connection string: asyncpg
  prepared statements break behind a transaction pooler. TLS required.
- Steps:
  1. Spike first (15 min): deploy a hello build with the proxy rule to a
     test backend and confirm `Set-Cookie` passes through the proxy and the
     cookie is sent back. If not, stop and rethink before anything else.
  2. Config, no app logic: `netlify.toml`; settings for TLS on the DB URL
     (`?ssl=require` for asyncpg); drop `railway.toml`; keep the Dockerfile
     for the backend host; `.env.example` notes. `frontend_dist` stays for
     local runs where FastAPI serves the build.
  3. Latency: the proxy times out at 26 s. Add a turn deadline (about 22 s)
     that ends the turn with a clear "taking too long, please retry" 504
     instead of a proxy error, and lower the OpenAI client timeout so retries
     fit. Measure p95 turn time on the live setup.
  4. Migrations and seed run as the backend's release or start command.
  5. Two demo accounts (`demo_alice`, `demo_bob`) seeded with a few
     preferences so reviewers see memory at once; documented in README.
  6. Update CLAUDE.md stack line, `docs/architecture.md` overview, README
     run/deploy notes, `docs/requirements.md` R9/D1, and ADR index.
- Done when: the baseline works on the Netlify URL from a fresh browser
  (login, memory across chats, a correction, isolation, an allergen block),
  and a chat turn stays under the proxy timeout.

## Phase 7: Part 2, reliability and evals (about 2.5 h)
- Eval cases per category, deterministic graders, runner, committed results.
- Run, find failures, fix the system, run again. Keep the before/after.
- `docs/eval-report.md` with per-category results and explained failures.
  Accept ADR 0014.
- Done when: the report shows per-category results and at least one real
  improvement measured before and after.

## Phase 8: Submission (about 1.5 h)
- README: local setup, architecture, key decisions (link ADRs), setup
  requirements, known limitations, demo accounts.
- Video 8 to 12 minutes following brief section 6.3.
- Drive folder; check every link from a logged-out browser.

## Out of scope (deliberately)
Placing real orders or payments, multiple restaurants, voice, Arabic UI,
dark theme, real authentication, admin menu editing. Each is noted in README
limitations.
