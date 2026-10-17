# 0009: Allergens and diet are enforced in code

- Status: Accepted
- Date: 2026-10-17

## Context
A wrong allergen recommendation is the one failure that can hurt someone.
Prompt instructions are followed most of the time, not all of the time.

## Decision
Allergies and diet are hard constraints, enforced twice:
1. `search_menu` applies the user's hard constraints server-side, from the
   stored profile, whatever arguments the model sends.
2. `safety/` checks every recommended item ID before the reply is returned.
   Failing items are removed and logged.
Allergens use a fixed vocabulary; user wording is mapped to it at extraction.
Dislikes, spice and budget stay soft and are left to the model's judgment.
`may_contain` items get a warning and a suggestion to confirm with staff.

## Alternatives considered
- Prompt-only rules: simpler, but no guarantee and nothing to prove.
- Enforce everything (including dislikes) in code: removes the model's ability
  to reason about trade-offs a user may accept.

## Consequences
- The guarantee is testable, which makes it strong evidence for Part 2.
- The user cannot be recommended an item with their allergen even if they ask.
  The agent can describe it, with a warning, but not recommend it.
