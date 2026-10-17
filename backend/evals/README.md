# evals

The Part 2 eval suite (ADR 0014, rules in `.claude/rules/evals.md`). It runs
the real agent and model against the local Postgres and grades each turn.
Results and their explanation: `docs/eval-report.md`.

## Run
```
docker compose up -d db                     # from the repo root
uv run python -m evals.run --runs 3 --label after
uv run python -m evals.run --category grounding --runs 1
uv run python -m evals.run --ids recall-peanut,update-budget
```
The runner refuses a non-local database. Each case runs through
`handle_message` (the `/api/chat` path minus HTTP) inside a transaction that
is rolled back, so nothing is left in the DB. It costs real OpenAI calls.

## Files
- `cases/<category>.yaml`: the cases, one file per category. Each lists its
  users and steps (`say`, optionally `new_conversation` or
  `into_conversation_of`), what each turn must satisfy (`expect`), and the
  facts each profile must hold at the end (`profiles`). Expectations are
  written before any run and never read from the DB. Cases written after the
  first baseline say `added_after_baseline: true`.
- `case_model.py`: the case schema and loader. Unknown fields are errors.
- `harness.py`: runs one case and records a transcript (`transcript.py`).
- `graders/`: `cards.py` (allergens, may-contain warnings, diet, card count,
  price limit), `prices.py` (prices in the reply text), `memory.py` (stored
  facts), `judge.py` (LLM judge for what the reply text claims; stores its
  reasoning). `grade.py` applies the checks a case asks for.
- `report.py`: per-category table. A case passes only if every check passes
  in every run (the worst-run view the rules require for safety).
- `results/<date>-<model>-<label>.json`: every run with transcripts, committed.

Expectation choices worth knowing:
- `forbid_allergens` is also used for a strong dislike ("can't stand
  mustard"), because the user asked never to get it.
- `max_price_sar` treats a stated budget as a limit for cards.
