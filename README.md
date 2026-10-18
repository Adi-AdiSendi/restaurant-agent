# Foodics Order Assistant: a restaurant ordering assistant that remembers you

An AI assistant that helps people choose what to order from a restaurant menu.
It learns their preferences through normal conversation, remembers them across
independent conversations, accepts corrections, and never recommends a dish
that breaks a stated allergy or diet. Built for the AI Engineer take-home.

Version 2 (in progress, `docs/plan.md`) adds six fictional restaurants, the
kinds of business Foodics serves: Corner Table (the v1 menu), Stack & Smash
(burgers), Shawarma Street, Golden Dragon (Chinese), Red Sea Catch (seafood)
and Bean & Bloom (cafe). Their dishes have real-world choices (bun, protein,
milk, sides, extras) and removable ingredients, and the allergy and diet
rules cover every choice.

**Live: https://restaurant-agent.netlify.app**

| Demo login | PIN | Profile |
|---|---|---|
| `demo_alice` | `1234` | peanut allergy, vegetarian, mild spice (an older "hot" shows as replaced) |
| `demo_bob` | `5678` | empty, to show isolation |

Any other username creates a fresh profile with the PIN you choose. The demo
accounts are reset on every backend deploy. The app runs on free hosting: if
nobody used it for a while, the first load shows "Starting the server" for up
to a minute.

## Try it (about 5 minutes)
1. **Memory and personalisation.** Log in as `demo_alice`, ask "What should I
   get today?" The picks are vegetarian, peanut-free and mild without you
   saying so. The side panel shows what is remembered.
2. **Safety.** Ask "Can I get the Thai Peanut Noodle Bowl?" It explains why not
   and offers an alternative. No card for it ever appears.
3. **Updating a preference.** Say "I'm vegan now." The reply confirms the
   change, the panel shows vegan, and Preferences lists vegetarian as
   updated earlier.
4. **Memory across conversations.** Click "New chat" and ask "Any dessert for
   me?" Only vegan desserts come back, from what you said in the other chat.
5. **Learning naturally.** Log out, log in as a new name, and just chat: "I'm
   allergic to sesame and I love spicy food, what's good?" Then open a new chat
   and ask "What should I get?"
6. **Isolation.** Log in as `demo_bob`: his profile is empty and nothing from
   Alice or you carries over.
7. **Restaurants and options.** Open Bean & Bloom from the home page and say
   "I'm allergic to dairy, can I have a latte?" The latte card lists every milk
   and strikes through whole, skimmed and lactose-free (all dairy). At Golden
   Dragon, `demo_alice` asking for kung pao "without the peanuts" is refused:
   leaving an ingredient out never removes an allergen.
8. **Order a meal.** On the menu (or from a card in the chat), choose options:
   the price updates as you go. Picking whole milk with a dairy allergy asks
   "Add it anyway?" before it goes in. Open the cart, check out for pickup,
   and the order appears under Orders with its status. Adding a dish from
   another restaurant asks before it empties your cart.
9. **Order by chat.** At Stack & Smash, say "I don't like pickles", then "Add
   a Classic Smash with a single patty and a brioche bun." The card under the
   reply says the pickles were left out, and the cart updates. "Make that two",
   then "Place my order": the assistant shows a checkout card, and only its
   button places the order. With a dairy allergy, "add a latte with whole milk"
   is refused and explained.
10. **See the menu.** At Bean & Bloom, with a dairy allergy saved, ask "What
    coffee do you have?" A menu block lists every coffee with its photo;
    the ones that cannot be made without dairy are greyed with the reason and
    have no Add button, and the assistant also recommends a few that fit.
    Dishes with nothing to choose have a one-click "Add".
11. **Speak your order.** Press the mic next to Send and say "Add a small
    latte with oat milk". The words appear in the message box as you speak;
    check them and press Send. Turn on **Auto** next to the mic to send what
    you say as soon as you stop speaking.
12. **Tastes and calories.** Say "I don't eat meat on Fridays and I'm keeping
    under 1800 calories a day". "What I remember" shows both, with today's
    ordered calories against the goal. Every dish shows its estimated kcal;
    turn on **Matches my tastes** on the menu to hide dishes against your
    dislikes, budget, spice, today's day rules or the calories left today.
13. **Order for me.** With something already in the cart, ask "Empty my cart and
    order me a Classic Smash with a single patty". At Bean & Bloom, ask for "5
    Khalas dates": they come in boxes of 3, so the assistant asks whether you
    want 6 (or 3) before adding anything.
14. **Edit by hand.** Open **Preferences** in the header. Everything the chat
    learned is there, and anything the chat can change you can change here:
    tick an allergy, pick a diet or spice level, set a budget or calorie goal,
    add likes and dislikes, and add days you avoid or want a food ("Fridays:
    fish"). Removing an allergy asks first. Then ask the chat "What should I
    get?": it uses the edited profile. Say "no fish on Fridays" in the chat,
    and the page shows the day like replaced.

## How it works
```
Browser (React) -> Netlify (static UI, /api/* proxy) -> FastAPI on Render -> Postgres (Netlify DB)
                                                           |
                                                           +-> OpenAI Responses API (gpt-6-luna)
```
One chat turn (`backend/app/agent/chat_turn.py`), in one DB transaction:
1. Load the user's active preferences (`user_id` comes from the session cookie only).
2. An extraction call turns the new message into memory operations (add,
   supersede, remove), validated and applied before the reply is written.
3. The model gets the profile, the conversation and, if memory just changed,
   a note saying what changed. It searches the menu with tools.
4. Allergies and diet are merged into every menu search in code, and every
   recommended item is checked again before it is shown.
5. The model answers with item IDs only; the UI renders each card (name,
   price, ingredients, allergens) from the database.

More detail: [docs/architecture.md](docs/architecture.md).

## Key technical decisions
Each links to its decision record in [docs/decisions/](docs/decisions/README.md).
- **Grounding by item ID** ([0010](docs/decisions/0010-grounding-by-item-id.md)):
  the model cannot invent a dish or a price, because cards come from the DB.
- **Allergens and diet enforced in code, not in the prompt**
  ([0009](docs/decisions/0009-hard-constraints-enforced-in-code.md)): a filter on
  every search plus a guard on every card.
- **Cart and orders on the server** ([0019](docs/decisions/0019-cart-orders-and-confirmed-checkout.md)):
  prices are always computed from the menu, a choice that breaks your
  allergies or diet needs your consent, and only your checkout button
  places an order.
- **Restaurants with options** ([0018](docs/decisions/0018-multiple-restaurants-with-options.md),
  [0020](docs/decisions/0020-tool-context-from-the-server.md)): a dish fits a guest
  only if its base fits and every required choice still has a safe option.
  Tools get the restaurant from the server, so a chat only sees its own menu.
- **Structured memory with supersession**
  ([0011](docs/decisions/0011-structured-memory-with-supersession.md),
  [0016](docs/decisions/0016-removed-status-and-target-checks.md)): typed facts
  (allergy, diet, budget, spice, likes, dislikes) with a status, so a correction
  replaces the old fact and the history stays visible.
- **Chat parity** ([0026](docs/decisions/0026-chat-parity.md)): whatever the
  chat can change, you can change by hand on the Preferences page or in the
  cart, through the same code. A test fails if a new chat ability has no
  manual route.
- **Username + 4-digit PIN** ([0013](docs/decisions/0013-identity-username-and-pin.md)):
  enough to identify returning users for a demo, nothing more.
- **Python, FastAPI, Postgres, React** ([0002](docs/decisions/0002-frontend-react-vite-typescript.md),
  [0003](docs/decisions/0003-backend-python-fastapi.md),
  [0004](docs/decisions/0004-database-postgresql.md)) and **gpt-6-luna**
  ([0005](docs/decisions/0005-llm-gpt-6-luna.md)).
- **Free hosting: Netlify + Render + Netlify DB**
  ([0017](docs/decisions/0017-deploy-netlify-with-api-proxy.md)): the UI on
  Netlify proxies `/api` to the unchanged backend, so the cookie stays
  first-party; a 22 s turn deadline fits the proxy's 26 s limit.
- **Small files, one-way dependencies** ([0007](docs/decisions/0007-line-limits.md),
  [0008](docs/decisions/0008-feature-folders-and-dependency-direction.md)),
  checked in CI ([0012](docs/decisions/0012-quality-gates-in-ci.md)).

## Part 2: reliability and evaluation
**Problem.** An assistant that remembers people can fail quietly: recommend a
dish with a stored allergen, invent a price, keep an outdated fact, or mix two
users' memories. A demo hides these failures. Without measurement, "it works"
is a claim.

**Why this over other directions.** It protects the promises the baseline
makes (safety, grounding, memory, isolation), and the brief values evidence
over claims. Voice, integrations or scale would add surface area before proving
the core works.

**Scope.** An eval suite in `backend/evals/`
([ADR 0014](docs/decisions/0014-part-2-reliability-and-evals.md)):
- 56 cases in 8 categories: allergen safety, diet compliance, grounding,
  memory recall, preference update, isolation, extraction precision, and
  ordering (added in v2 phase 12; the table below is the Part 2 run).
- Each case runs 3 times through the real chat path and model, in a
  rolled-back DB transaction.
- Graders are code wherever possible; an LLM judge only reads the reply text,
  and its reasoning is stored.
- A safety case must pass in every run.

Left out: production observability, load testing, automatic prompt tuning.

**Results.** Full report with transcripts and caveats:
[docs/eval-report.md](docs/eval-report.md).

| | Before | Final |
|---|---|---|
| Allergen, diet and isolation safety (18 cases) | 18/18 | 18/18 |
| Grounding, memory recall, extraction (18 cases) | 18/18 | 18/18 |
| Preference update (6 cases) | **4/6** | **6/6** |
| Replies with no card and no question (36 original cases) | 18/159 | 11/159 |

- **What failed.** Memory changed silently. After "I'm vegetarian now, not
  vegan" or a new dairy allergy, the memory and the cards were right, but the
  reply never told the user, so a wrong extraction would go unnoticed.
- **The fix** ([context.py](backend/app/agent/context.py)). The turn compares
  the profile before and after extraction and tells the reply model what
  changed. The reply confirms it in one sentence and, for an allergy or a
  diet, says the pick fits it.
- **A lesson along the way.** The first version passed every graded check
  but made replies shorter (dead ends 18 to 43). A code review caught it. It
  is now measured, and the final version is better than the start (11).

## Setup requirements
- Docker (for the local Postgres), [uv](https://docs.astral.sh/uv/), Node 22+.
- An OpenAI API key with access to the model in `OPENAI_MODEL`.
- Settings come from the environment or a repo-root `.env` (see `.env.example`):

| Variable | Needed | Meaning |
|---|---|---|
| `OPENAI_API_KEY` | yes | OpenAI key |
| `OPENAI_MODEL` | yes | model ID, `gpt-6-luna` |
| `DATABASE_URL` | yes | Postgres URL; plain `postgres://` URLs are converted |
| `SESSION_SECRET` | in production | 32+ random characters to sign cookies |
| `APP_ENV` | no | `development` (default), `test` or `production` |
| `TURN_DEADLINE_SECONDS` | no | per-turn limit, default 22, must stay under 26 |

## Run locally
```
cp .env.example .env            # fill in OPENAI_API_KEY
docker compose up -d db
cd backend && uv sync && uv run alembic upgrade head && uv run python -m scripts.seed_menu
uv run uvicorn app.main:app --reload          # API on http://localhost:8000
cd ../frontend && npm install && npm run dev  # UI on http://localhost:5173
```
Checks (the same as CI):
```
cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest
cd frontend && npm run lint && npm run typecheck && npm test
python scripts/check_line_limits.py
```
Evals (real OpenAI calls, local DB only): `cd backend && uv run python -m evals.run --runs 3`.

## Deployment
- Netlify builds `frontend/` and proxies `/api/*` to the backend (`netlify.toml`).
  A scheduled function pings the backend every 10 minutes so it stays awake.
- Render runs `backend/` with its native Python runtime (`render.yaml`, no
  Docker). Its build runs migrations, the menu seed and the demo-user reset.
- Secrets live only in the Render dashboard: `DATABASE_URL` (the direct, not
  pooled, Netlify DB string) and `OPENAI_API_KEY`; Render generates `SESSION_SECRET`.
  Netlify needs no environment variables: its secret scan fails the build
  when a backend value (even `APP_ENV`) appears in the frontend files.
- Netlify deploys every push to `main`; Render deploys when `backend/` changes.

## Known limitations
- **Free hosting:** the backend sleeps after 15 idle minutes. A ping keeps it
  awake; if one is missed, the first load waits for the server to start
  (measured: 33 s, then a 7.7 s first answer). Netlify DB
  Free has a monthly compute cap; the app keeps no idle connections so it can sleep.
- **Turn time:** a turn must finish in 22 s or it ends with "took too long,
  please try again" (measured p95 per eval category is 6 to 10.4 s).
- **Identity:** username and PIN with no lockout; sessions are signed cookies
  valid for 30 days. Fine for a demo, not for production. The demo PINs are
  public, so anyone can change the demo profiles until the next deploy resets them.
- **Text vs cards:** the safety guard checks recommended items, not the reply
  text. Cards are always safe; the text could in rare cases name an unsuitable
  dish. The evals found no such case.
- **Conversations:** reloading the page starts a new conversation; old ones
  are kept but not listed. Memory carries over either way, across restaurants.
- **Ordering:** no payment ("pay at the counter"), and the status moves on
  by time, not by a kitchen. One cart per guest, at one restaurant. Search
  price limits apply to the base price; options can add to it. The eval price
  grader only checks dish prices, not option prices.
- **Ordering by chat:** the chat can add, change and remove cart lines, and
  empty the cart when the guest asks or agrees (for example to replace a
  cart from another restaurant), but it never places an order: the guest's
  checkout button does. Dishes sold in packs (dates, in boxes of 3) only take
  whole packs; the chat asks before rounding. While a chat turn
  changes the cart, a click on the cart waits for the turn (at most 22 s),
  and the reply's cart can briefly hide a click that finished first, until
  the next change or reload. Checkout refuses a total the guest did not see.
- **Order records:** an order does not record that the guest added a dish
  despite a warning (that needs a new column). A dish removed from the menu
  drops out of carts without a notice.
- **Concurrency:** a turn holds one DB transaction across its LLM calls, so
  each open turn uses one connection. Fine at demo scale.
- **Evals:** 56 cases, written by the same team that built the system, and the
  judge is the same model it grades. See the report for what is not covered.
- **Photos:** 91 of the 109 dishes and covers have an openly licensed
  Openverse photo of a similar dish, not the restaurant's own; the rest show
  an icon. The user reviewed each one. Credits: [docs/photo-credits.md](docs/photo-credits.md).
- **Voice:** English only. By default the guest checks the words and presses
  Send, so a misheard order never changes the cart unseen; the **Auto**
  toggle (remembered in the browser) sends at once instead. Chrome and Edge use the browser's
  own speech recognition (which may send audio to the browser maker);
  other browsers record a clip (up to 20 s) that the server sends to
  OpenAI's transcription. No spoken replies.
- **Calories and tastes:** calories are my estimates from typical portions,
  not lab values, and always labelled as estimates. Day rules, the calorie
  goal, dislikes, budget and spice are soft: they add notes and power the
  "Matches my tastes" filter, but never block an order (ADR 0025). "Today"
  is Riyadh time; the daily total counts only orders placed in this app.
- **Cut for the deadline:** a mobile layout pass, Arabic voice, and the
  restaurant and personal CRM pages (plan phases 14, 16 and 17). The app
  works on a phone but was not tuned for one.
- **Brand:** the Foodics name, logo and colours are used for this prototype
  only (ADR 0015). The restaurants are fictional. Not handled: real
  payments, Arabic.

## Repository map
| Path | What |
|---|---|
| `backend/app/` | FastAPI app: `api`, `agent`, `tools`, `memory`, `safety`, `orders`, `menu`, `users`, `db` |
| `backend/evals/` | eval cases, graders, runner, committed results |
| `backend/data/restaurants/` | one menu file per restaurant |
| `backend/tests/` | 800+ tests, real Postgres, fake LLM |
| `frontend/` | React + Vite + TypeScript UI, Netlify keep-awake function |
| `docs/` | [architecture](docs/architecture.md), [decisions](docs/decisions/README.md), [eval report](docs/eval-report.md), [challenges we faced](docs/challenges.md), [requirements trace](docs/requirements.md), [plan](docs/plan.md) |
