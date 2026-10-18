# Build plan

Budget: about 10 to 12 focused hours inside the 72-hour window.
Rule: the baseline must work end to end (deployed) before Part 2 starts.
Every phase ends with all checks green and a `code-reviewer` pass.

**Current phase: 18** (v2; phases 9 to 13 done, 15 done in English only, 14, 16 and 17 cut for the deadline; v1 phases 0 to 8 are below, the video moved to phase 18)

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
- Status: README done 2026-10-17. The video and the Drive folder moved to
  phase 18, after v2.

## Version 2 overview

Goal: show the range of businesses Foodics serves and a full ordering
experience, one feature per phase. Decided with the user on 2026-10-17:
- The guest picks one restaurant, then orders. Menu, cart and chat are
  scoped to it.
- Dish photos are free stock photos.
- Voice works in English and Arabic; the screens stay in English.
- The CRMs use simulated order history, labelled as simulated.

Same rules as v1:
- Every phase ends green, reviewed and deployed.
- `main` stays deployable throughout.

Reused from sibling projects, adapted rather than rebuilt:
- **Voice:** the speech and recorder code and the transcribe route from
  `Aviation-Services/site/concierge` and `server/chat` (portfolio has the same code).
- **Chat cart pattern:** two patterns, because neither app has a cart:
  - server-held state shown to the model each turn, and a confirm card, from Aviation-Services;
  - strict write tools and cards built from tool results, from Employee-Management.
- **Charts:** the SVG `DailyChart`, `BarList`, `StatTile` and `DataTable` from
  `Aviation-Services/site/console/reports`.

## Phase 9: v2 foundations (about 2 h)
- ADRs 0018 to 0023:
  - multiple restaurants with options;
  - cart, orders and a confirmed checkout;
  - tool context from the server;
  - React Router;
  - stock photos;
  - staff role.
- This plan, the "Out of scope" list and the stack lines in CLAUDE.md.
- Still open from v1: remove `docs/task/` from the git history before the
  repo goes public. It needs the user's go-ahead for the rewrite and force-push.
- Done when: the ADRs are accepted and this plan is committed.
- Status: done 2026-10-17. The `docs/task/` history rewrite is still open; it
  needs the user's permission.

## Phase 10: many restaurants and options (about 7 h)
- **Data:** one file per restaurant in `backend/data/restaurants/<slug>.json`.
  - Corner Table stays unchanged, so the v1 tests and evals keep working.
  - Five new brands of about 15 dishes each: burger house, shawarma and
    grill, Chinese, seafood, and a cafe (sizes, milks, syrups).
- **Migration 0003:**
  - a `restaurants` table;
  - `menu_items.restaurant_id`, with names unique per restaurant;
  - categories per restaurant;
  - option groups with min/max;
  - options with price change, allergens, may-contain and diet flags;
  - removable ingredients.
- **Seed:** upserts by (restaurant, name) and never touches another restaurant.
- **Resolver:** `menu/configure.py` is pure and gives the priced, checked
  configuration. Removing an ingredient never removes an allergen.
- **Safety:** the guard blocks a dish only when no way of ordering it fits;
  options carry their own conflicts and trace warnings. The resolver joins
  the request path with the cart in phase 11.
- **Agent:**
  - conversations belong to a restaurant;
  - tools take a `ToolContext` (ADR 0020);
  - `get_item` returns the options;
  - the prompt names the current restaurant and lists the others.
- **Tests:**
  - the resolver;
  - an exhaustive guard test over every item and option;
  - seed isolation;
  - an eval case where an add-on brings in an allergen.
- Done when: the six menus are seeded locally and live, and each
  restaurant's chat recommends only its own dishes.
- Status: done 2026-10-17. 103 dishes (Corner Table 18, then 15 to 20 each),
  304 options. 774 backend and 42 frontend tests. Evals: the 5 new cases plus
  every safety category, 3 runs, all pass, before and after the review fixes
  (`phase10`, `phase10-fixes`).
  - **Review fixes:**
    - Option traces (oat milk, gluten-free bread, falafel, fries) did not
      reach the guest; now they are on each option, and on the card when
      unavoidable.
    - Meat-only dishes were flagged vegetarian; a data test now requires
      base diet flags to be reachable.
    - The model's own diet filter now checks options.
    - Text search covers option names.
    - A stale chat start could win a fast restaurant switch.
    - `evals/run.py` was over 100 lines.
  - **Live run on gpt-6-luna, fresh user, one chat per restaurant:**

    | Restaurant | Turn | Result |
    |---|---|---|
    | Bean & Bloom | 9.3 s | "dairy allergy, latte?": latte with oat milk; whole, skimmed and lactose-free struck through |
    | Golden Dragon | 5.2 s | spicy tofu: Mapo Tofu, base steamed rice or rice noodles |
    | Shawarma Street | 5.1 s | wrap with chicken; Akkawi cheese marked "not for you" (the dairy allergy carried over) |
    | Red Sea Catch | 4.9 s | hammour; tandoori and lemon butter marked dairy |
    | Stack & Smash | 5.7 s | "no pickles": Beyond Smash, potato bun or lettuce wrap, then a question |
    | Corner Table | 4.8 s | dairy-free desserts only: Mango Sorbet, Fresh Lemon Mint |

## Phase 11: browse, cart and checkout by hand (about 9 h)
- **Backend:** `app/orders/` holds carts, cart lines, orders and order lines
  (ADR 0019).
  - Prices are recomputed from the DB.
  - Order lines are snapshots.
  - The order status is derived from the time since placement.
- **Checkout:** pickup or dine-in, "Pay at the counter", placed only by the
  guest's button.
- **API:**
  - restaurants and their menu;
  - the cart (get, add, change, remove, clear);
  - orders (place, list, detail).

  All of it is scoped by the session user. A manual add that conflicts with
  the guest's profile needs an acknowledged warning.
- **Frontend** (React Router, ADR 0021):
  - restaurants;
  - a menu with category tabs, search and a "fits my profile" filter;
  - an item sheet with options and a live price;
  - a cart drawer, checkout and orders;
  - the chat as a panel on the restaurant page.

  Built mobile first; the full mobile pass is phase 14.
- **Tests:**
  - cart isolation between users;
  - price recompute;
  - option validation;
  - conflict acknowledgement;
  - frontend flows.
- Done when: a guest can pick a restaurant, configure a dish, check out and
  see the order on the live site.
- Status (2026-10-17, end of session): code, tests (806 backend, 66 frontend),
  docs and the code-review fixes are committed. The review found consent
  that could cover a later conflict, a chat turn's user lock blocking
  checkout (FK key-share), stale cart warnings, non-modal dialogs and an
  optional single choice that could not be cleared; all fixed.
- Close-out (2026-10-18): OrderPage is keyed by order id and ignores a
  response after unmount; MenuPage is keyed by slug; the menu hook keeps
  only the latest response. Seven frontend tests added (73 in all), and
  three ordering limitations in the README. Reviewed by `code-reviewer`.
- Live check 2026-10-18 on the Netlify site, two fresh users, scripted
  through the API (Render was asleep: ready after 32 s):

  | Check | Result |
  |---|---|
  | latte, small, oat milk, pickup | added 0.9 s (19.00 SAR); order placed 0.9 s; cart empty after |
  | the order under Orders, and its page | listed 0.9 s; detail 0.9 s with Small, Oat milk |
  | another user opens that order | 404 |
  | "I am allergic to dairy", then whole milk | chat 7.8 s; add refused 409, reason dairy |
  | the same add with dairy accepted | added |

  The browser pass was not run: Claude in Chrome was not connected. The UI
  flow is covered by the frontend tests.
- Found after the close-out: the phase 10 and 11 UI was not live. Every
  Netlify deploy from 623186e to 241823c failed its secret scan, because
  backend variables copied into Netlify (`APP_ENV`'s value) matched a word in
  the frontend code. CI was green, so it went unnoticed. The user removed the
  backend variables from Netlify; the redeploy serves `index-DBz0ewEJ.js`
  with the phase 11 UI, and `/r/bean-and-bloom` and `/orders/1` load.
- Status: done 2026-10-18.

## Phase 12: ordering through the chat (about 7 h)
- **Tools:** `view_cart`, `add_to_cart`, `update_cart_line`,
  `remove_cart_line`, `recent_orders` and `propose_checkout`. The last one
  shows a checkout card; the model never places an order.
- **Checks on every add:** grounding (item and options from this restaurant)
  and the guard. A conflict is explained, never overridden.
- **Preferences:** a stored dislike that can be removed ("no pickles") is
  applied when adding, and the reply says so.
- **Each turn:**
  - the model sees the current cart;
  - cart writes join the turn's transaction;
  - the reply carries the cart and action cards built from tool results.
- **Frontend:**
  - action, cart and checkout cards in the chat;
  - the drawer updates from chat replies.
- **Evals:** a new `ordering` category:
  - add, change and remove;
  - an unsafe add is refused;
  - the dislike is applied;
  - no order is placed without the button;
  - carts are isolated.

  Also measure p95 turn time against the 22 s deadline.
- Done when: a full order can be built and changed by chat alone, and the
  ordering evals pass 3 of 3 runs.
- Status: done 2026-10-18.
  - **Built:**
    - six cart tools (`app/tools/`), each write in a savepoint of the turn;
    - the cart with line ids in the model's context;
    - replies carry action cards and the cart;
    - a chat checkout card whose button places the order.
  - **Decided with the user:** a cart from another restaurant is refused
    with a pointer to "Empty cart"; a removable dislike is left out and
    reported ("with pickles this time" keeps it).
  - **Review fixes:**
    - checkout refuses a total the guest did not see (`cart_changed`);
    - a conflicting line cannot be raised;
    - checkout is proposed only at the cart's restaurant;
    - dislikes match whole words.
  - **Evals:** ordering 9/9 cases over 27 runs, p95 8.0 s; every safety
    category passes every run. The full run caught a regression (the
    `add_to_cart` description made a disliked dish look fine to recommend),
    fixed and measured (`docs/eval-report.md`). Tests: 854 backend, 82 frontend.
  - **Live run** 2026-10-18 on the Netlify site (bundle `index-CjJDF6BI.js`),
    fresh user at Stack & Smash:

    | Turn | Time | Result |
    |---|---|---|
    | "I don't like pickles." | 10.1 s | stored |
    | add a Classic Smash, single, brioche | 6.4 s | added, "pickles left off" |
    | "Make that two." | 6.0 s | line set to 2, 64.00 SAR |
    | "Add classic fries too." | 5.0 s | asked regular or large |
    | "Regular, please." | 6.1 s | fries added, 76.00 SAR |
    | "Actually, remove the fries." | 3.9 s | removed, 64.00 SAR |
    | "Place my order for pickup." | 3.3 s to 5.0 s | checkout card, "not placed yet", 0 orders |
    | the card's button (API) | 0.6 s | order placed, 64.00 SAR |

    The browser click-through was not run (Claude in Chrome not connected);
    the live bundle was checked for the new UI strings.

## Phase 13: visuals (about 6 h)
- **Photos** (ADR 0024, which superseded 0022: no Pexels key):
  - Openverse candidates per dish, ranked by a script;
  - the user reviews every pick on a contact sheet;
  - WebP at 320 and 640 px under `frontend/public/menu/`;
  - credits in `docs/photo-credits.md`.

  Restaurant cover photos too.
- **Cards and menus:**
  - photo cards with a quick "Add" button;
  - recommendations scroll sideways;
  - a `show_menu(category)` tool for a grounded menu block in the chat.
- **States:** loading skeletons, empty states and an icon fallback for
  missing photos.
- Done when: every dish has a credited photo the user approved, or a
  deliberate icon, and the chat shows photo cards, menu blocks and cart cards.
- Status: done 2026-10-18.
  - **Photos:** Openverse search found candidates for 108 of 109 targets
    (after simpler and hand-written queries). The user reviewed every pick on
    a contact sheet: 52 changes, 17 set to no photo. I switched one more
    (Mapo Tofu, whose pick showed peanuts the dish does not have) with the
    user's approval. 91 photos, 4.1 MB, credited in `docs/photo-credits.md`.
  - **Built:** migration 0005 (`photo`), `show_menu` and menu blocks,
    `DishPhoto` with an icon fallback, quick Add, sideways cards, covers,
    skeletons.
  - **Review fixes:** quick Add only for dishes with nothing to choose or
    notice, waits while adding; traces on menu rows; licence and owner
    checks on photos; the import writes only when complete.
  - **Evals:** the first full run caught menu blocks replacing
    recommendations for guests with allergies (no unsafe card); fixed. Final
    run: every safety category passes every run, grounding 8/8, ordering
    26/27 (one judge-only miss, see `docs/eval-report.md`). Tests: 878
    backend, 94 frontend.
  - **Live** 2026-10-18 (bundle `index-CwYAHszg.js`): photos load from
    `/menu/` as WebP; a dairy guest's "What coffee do you have?" gave the
    coffee block (2 of 8 greyed) and 3 dairy-free cards in 8.3 s; "cakes and
    pastries" gave its block (3 of 4 greyed) and Vegan Banana Bread in 5.1 s.
    The model once said the block is "above" the reply; it is below.

## Phase 14: mobile friendly and fluid sizing (about 4 h)
- Status: cut for the deadline (2026-10-18, the user's decision).
- **Sizing:**
  - fluid type and spacing (`clamp()`);
  - `100dvh` and safe-area insets;
  - 44 px touch targets;
  - `srcset` images.
- **Phone layout:**
  - a bottom tab bar;
  - the cart as a bottom sheet;
  - the item sheet full screen;
  - the chat full height with the composer above the keyboard;
  - tables become cards.
- **Desktop:** menu and chat side by side.
- **Checks:** a Playwright smoke test (new dev dependency) at 360, 768 and
  1440 px. It checks for no sideways scroll and that the key flows can be
  reached. Screenshots go in `docs/screenshots/`.
- Done when: every page passes at the three sizes, plus a manual check on a
  real phone.

## Phase 15: voice input, English and Arabic (about 5 h)
- Status: done 2026-10-18 in English only; Arabic was cut for the deadline.
  `POST /api/transcribe` (OpenAI, login, 10 MB cap, 20 clips per 5 minutes)
  and a mic in the composer ported from Aviation-Services: browser speech
  recognition where available, else a recorded clip. The text goes into the
  box and the guest sends it (no auto-send). Tests: 5 backend, 3 frontend.
- **Frontend:** port `speech`, `record` and `useVoice` to TypeScript under
  `features/voice/`.
  - A mic button with an EN/AR chip.
  - Auto-send or Review.
  - Live text in the input.
  - Messages for denied permission and no speech; the source ignored them.
- **Backend:** `POST /api/transcribe`:
  - login required;
  - a 10 MB cap;
  - a per-user rate limit;
  - the `OPENAI_TRANSCRIBE_MODEL` setting (default `whisper-1`).
- **Arabic:** replies in the guest's language, with dish names as on the
  menu. Extraction maps Arabic to the English vocabulary, so allergies stay enforced.
- **Tests and evals:**
  - a fake recognizer and a fake transcriber in the tests;
  - Arabic eval cases for extraction, safety and a chat add-to-cart.
- Done when: Chrome uses on-device speech, Firefox and Safari use the
  server, and the Arabic evals pass.

## Phase 16: restaurant CRM (about 8 h)
- Status: cut for the deadline (2026-10-18). ADR 0023 (staff role) was not built.
- **Staff role** (ADR 0023): `users.role`, `demo_staff` and `require_staff`.
- **Simulated history:** `scripts/seed_demo_orders.py`.
  - About 40 personas over 12 weeks, deterministic.
  - Rows are marked `is_simulated` and regenerated relative to today on each
    build.
  - The UI says "includes simulated orders".
- **Metrics:** SQL in `app/insights/`, by restaurant and period (7, 30, 90 days):
  - orders, revenue and average order value;
  - by day and by hour;
  - top items, add-ons and removals;
  - weekday against weekend;
  - repeat rate;
  - segments by diet, allergy and spice, each shown only with 5 or more guests.
- **UI:** `/staff`.
  - A KPI strip, a daily chart, bar lists and segment tables, each with a table view.
  - An orders list.
- **Tests:** metrics on fixed fixtures, and staff-only access.
- Done when: `demo_staff` sees the trends and segments for each restaurant on
  the live site.

## Phase 17: personal CRM (about 6 h)
- Status: cut for the deadline (2026-10-18).
- **`/me` page:**
  - favourite restaurants, cuisines and dishes;
  - spend over time;
  - when I order (each cuisine by weekday or weekend, and time of day);
  - the memory panel.
- **Habits:** rules in code with evidence counts.
  - **Removal habits:** an ingredient removed in at least 80% of 4 or more
    orders, with exceptions where the rate is under 20%. Example: "no pickles
    except in salads".
  - **Time habits:** a cuisine at least 2x more likely at weekends, over 3 or
    more orders. Example: "Chinese at weekends".
- **Using habits:** the agent gets them as soft context with their evidence,
  never as hard constraints. "Save as preference" turns one into a memory fact.
- `demo_alice` gets a simulated history that shows both habits.
- **Tests and evals:** habit rules on fixtures, and an eval where the agent
  offers a habit without forcing it.
- Done when: Alice's `/me` shows both habits with their evidence, and the
  chat uses them.

## Phase 18: evals, docs and submission v2 (about 4 h)
- A full eval run (all categories, 3 runs) and an updated eval report.
- README, architecture, requirements, challenges and fresh screenshots.
- The video.
- Done when: everything is green, deployed and documented.

## Out of scope (deliberately)
- Real payments.
- Arabic, spoken or on screen.
- Spoken replies.
- Dark theme.
- Real authentication.
- Admin menu editing.
- One cart across several restaurants.

Each is noted in the README limitations.
