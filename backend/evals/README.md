# evals

The Part 2 eval suite (ADR 0014, rules in `.claude/rules/evals.md`). It runs
the real agent and model against the local Postgres and grades each turn.

- `cases/<category>.yaml`: the cases, one file per category. Each case lists
  its users and steps (`say`, optionally `new_conversation` or
  `into_conversation_of`), what each turn must satisfy (`expect`), and the
  facts each profile must hold at the end (`profiles`). Expectations are
  written before any run and never read from the DB.
- `case_model.py`: the case schema and loader. Unknown fields are errors.

Expectation choices worth knowing:
- `forbid_allergens` is also used for a strong dislike ("can't stand
  mustard"), because the user asked never to get it.
- `max_price_sar` treats a stated budget as a limit for cards.
