# 0025: Soft tastes: day rules, a calorie goal and estimated calories

- Status: Accepted
- Date: 2026-10-18

## Context
The user asked for more from "What I remember about you": remembered choices
that filter the menu, foods avoided on a particular day ("no meat on
Fridays"), and calorie tracking. No dish had calorie data.

## Decision
- Two new soft preference kinds (migration 0006):
  - `day_dislike`, stored as `"<weekday>: <food>"`;
  - `calories`, a daily goal from 800 to 6000 kcal.

  Allergies and diet stay the only hard rules (ADR 0009); these never block.
- "Today" means Riyadh time (UTC+3, no daylight saving), in `menu/clock.py`.
  A day rule for today works like a dislike; "meat" means not vegetarian.
- Calories are estimates I wrote from typical portions (migration 0007):
  - `kcal` per dish and `kcal_delta` per option;
  - a `kcal` snapshot on each order line, summed for today's total.

  The UI always says "estimate".
- The menu carries soft `taste_notes` per dish:
  - a disliked ingredient that cannot be left out;
  - today's day rules;
  - over budget;
  - spicier than liked;
  - more than the calories left today.

  "Matches my tastes" hides those dishes. Liked dishes get a badge.

## Alternatives considered
- Day rules as hard constraints: stricter, but they would change the safety
  code and the consent flow for a preference, not a medical need.
- Calories from a nutrition API: real data, but no key, cost, and matching
  our invented dishes to foods would still be a guess.

## Consequences
- Calorie numbers are approximate and must never be presented as exact.
- The daily total counts only orders placed in this app.
