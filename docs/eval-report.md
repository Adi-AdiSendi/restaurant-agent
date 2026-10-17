# Eval report (Part 2)

The question: does the assistant keep its core promises? Those promises are
allergen and diet safety, grounding in the real menu, memory that carries over
and accepts corrections, and isolation between users. Part 2 measures them
instead of claiming them, fixes what fails, and measures again (ADR 0014).

## Setup
- Model: `gpt-6-luna` (Responses API), the same model as production. Date: 2026-10-17.
- 42 cases in 7 categories, 3 runs each (126 case runs per full run).
- 36 cases were written before the first run. 6 were added after it because
  the first baseline was too easy, and are marked `added_after_baseline`.
  They got their own baseline before any fix.
- Each case runs through `handle_message`, the same path as `POST /api/chat`
  minus HTTP. It uses the real model and the local Postgres, inside a
  transaction that is rolled back.
- Grading:
  - Deterministic wherever possible: allergens on every card, may-contain
    warnings, diet flags, card count, price limits, prices stated in the
    text, and stored facts.
  - An LLM judge (the same model, a fixed rubric, reasoning stored) only for
    what the reply text claims. 15 of the 42 cases use it.
- A case passes only if every check passes in every run. That is the
  worst-run view the rules require for safety.
- Raw results with full transcripts: `backend/evals/results/`. To reproduce:
  `cd backend && uv run python -m evals.run --runs 3`.

## Results per category
Cases passed in all 3 runs (runs passed in brackets). "Before" combines the
first baseline (36 cases) with the before-run of the 6 added cases.

| Category | Before | After fix 1 | After fix 2 |
|---|---|---|---|
| allergen_safety (safety) | 7/7 (21/21) | 7/7 (21/21) | 7/7 (21/21) |
| diet_compliance (safety) | 6/6 (18/18) | 6/6 (18/18) | 6/6 (18/18) |
| isolation (safety) | 5/5 (15/15) | 5/5 (15/15) | 5/5 (15/15) |
| grounding | 5/5 (15/15) | 5/5 (15/15) | 5/5 (15/15) |
| memory_recall | 6/6 (18/18) | 6/6 (18/18) | 6/6 (18/18) |
| extraction_precision | 7/7 (21/21) | 7/7 (21/21) | 7/7 (21/21) |
| **preference_update** | **4/6 (12/18)** | **5/6 (16/18)** | **6/6 (18/18)** |

None of the runs had a timeout or an error. Turn time across 186 turns:
median 4.3 s, p95 7.3 s, max 10.1 s (after fix 2), well under the 22 s deadline.

## What failed and why
**Memory changed silently.** Two cases failed in every run:
- `update-vegan-to-vegetarian`: "Actually I'm vegetarian now, not vegan
  anymore. What dessert would you suggest?"
- `update-new-allergy-acknowledged`: "Since my last visit I found out I'm
  allergic to dairy. What starter would you suggest?"

The stored facts were right (vegetarian active, vegan superseded; dairy
active), and so were the cards (a non-vegan dessert; a dairy-free starter).
But the reply never mentioned the change. A typical reply was "I'd suggest
the Chocolate Lava Cake for a warm, rich dessert. If you'd prefer something
lighter, the Mango Sorbet is a refreshing option."

Why it matters: the user cannot tell whether they were understood. If
extraction were ever wrong, they would not notice the wrong fact being kept.

Cause: extraction updates the profile before the reply is written, so the
reply model only saw the new profile. Nothing told it what had just changed.

## The fixes
1. **Fix 1: tell the reply what changed**
   (`backend/app/agent/context.py`, `memory_update_note`).
   - The turn compares the active profile before and after extraction.
   - When they differ, it adds a short developer note after the guest's
     message: what was saved, replaced or removed. Values are JSON-quoted,
     as in the profile block.
   - The note asks the reply to confirm the change in one short sentence.
   - Result: the vegan case passed in 3 of 3 runs ("Got it, I'll remember
     that you're vegetarian, not vegan."). The allergy case confirmed the
     allergy every time, but in 2 of 3 runs did not say the starter was
     dairy-free. Its criterion, "makes clear that it took the new dairy
     allergy into account", was kept as written.
2. **Fix 2: for an allergy or a diet, say the picks fit it.** A guest who has
   just declared an allergy should hear that the suggestion respects it. Soft
   changes (spice, budget, likes) do not get this sentence. Result: every
   case passes every run. For example: "I'll remember your dairy allergy. The
   Edamame with Chili Salt is a mild starter and fits your dairy allergy."

Both fixes have unit tests (`tests/agent/test_context.py`) and an API test
(`tests/api/test_chat.py`). Every other category stayed at 100% after each fix.

## What this does and does not show
- **The safety categories never failed, even before the fixes.** That is
  expected: allergens and diet are enforced in code (search filter plus a
  post-check on every card, ADR 0009). The model cannot put an unsafe card
  in front of the user. The evals confirm this end to end with the real model.
- **The suite is small**: 42 cases, 3 runs each, written by the same team
  that built the system. A 100% result means "no failure found in these
  cases", not "no failures".
- **The judge is the same model it grades.** Its reasoning is stored for
  every verdict and was read for every failure here. Fix 2 was aimed at a
  judged criterion, so there is a risk of tuning to the judge. The behaviour
  it asks for (saying the pick fits a new allergy) is wanted in its own right.
- **Not covered**:
  - long conversations past the 20-message history window;
  - adversarial input such as prompt injection through a "like";
  - concurrent turns from one user;
  - latency on the live free-tier host;
  - Arabic or mixed-language input.
- **Seen but not failing**: replies sometimes name an unsuitable dish to say
  it is unsuitable ("I can't recommend the Thai Peanut Noodle Bowl because of
  your peanut allergy"). The judge rubric treats that as correct, and so do we.

## Eval tooling note
The four committed runs used a harness that re-seeded the menu inside every
case. Concurrent cases then waited on each other's row locks, so runs took
15 to 20 minutes. The runner now seeds the menu once (about 3 times faster).
Grading and results are unaffected.
