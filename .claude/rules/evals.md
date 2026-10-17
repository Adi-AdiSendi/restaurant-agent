---
paths:
  - "backend/evals/**"
  - "docs/eval-report.md"
---
# Eval rules

The eval suite is the evidence for Part 2. Its results go in the video and
README, so they must be honest and reproducible.

## Layout
- `evals/cases/<category>.yaml`: test conversations, one file per category.
- `evals/graders/`: one grader per check type.
- `evals/run.py`: runs cases against the real agent and writes results.
- `evals/results/<date>-<model>.json`: raw results, committed.

## Categories (report each separately)
- `allergen_safety`: never recommend an item containing a stored allergen.
- `diet_compliance`: vegetarian/vegan users get only compliant items.
- `grounding`: every recommended ID exists; no invented dishes or prices.
- `memory_recall`: a fact from conversation 1 is used in conversation 2.
- `preference_update`: a corrected fact replaces the old one.
- `isolation`: user B never sees user A's preferences.
- `extraction_precision`: no false memories ("my friend is vegan").

## Grading
- Prefer deterministic graders: check `recommended_item_ids` against the DB and
  the user's profile. These are exact.
- Use an LLM judge only for qualities code cannot check (did the reply
  acknowledge the update?). Give the judge a rubric and record its reasoning.
- Each case states its expected outcome before it runs. Never adjust a case's
  expectation after seeing a failure without noting it in the report.

## Reporting
- Report pass rate per category, never only an overall number. A high average
  can hide a weak category.
- Record model ID, date, case count and number of runs. LLM output varies, so
  run each case at least 3 times and report the worst run for safety categories.
- Include failures with their transcripts. Explain each one.
- Before/after comparisons use the same cases and model.
