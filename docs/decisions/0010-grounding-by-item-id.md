# 0010: Grounding by item ID and database-rendered cards

- Status: Accepted
- Date: 2026-10-17

## Decision
The model's final answer is structured: `{reply, recommended_item_ids}`. The
server validates each ID. The UI renders name, price, ingredients and
allergens from the database, never from the model's text.

## Why
- The brief forbids invented dishes, ingredients and prices. With ID-only
  answers, an invented dish cannot appear as a card, and prices on screen are
  always real.
- Grounding becomes checkable by code in evals.

## Consequences
- The model can still mention a detail in prose wrongly. The system prompt
  tells it to refer to cards for details, and evals check prose for prices
  that do not match the cited items.
