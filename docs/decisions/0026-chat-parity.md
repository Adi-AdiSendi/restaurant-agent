# 0026: Chat parity: whatever the chat can do, the guest can do by hand

- Status: Accepted
- Date: 2026-10-18
- Amends: [0025](0025-soft-tastes-day-rules-and-calories.md) (adds `day_like`)

## Context
The guest could change what the app remembers only by talking to the chat.
The extraction call adds, replaces and removes facts, but the UI could only
show them. A guest who wanted to fix a wrong fact, or did not want to chat,
had no way to do it. The cart and orders did not have this gap: every cart
tool already had a button.

The user asked for a Preferences page, for days when they want a food
("fish on Fridays"), and for this to become a rule of the architecture.

## Decision
- **Parity rule.** Every change the chat can make to the guest's data has a
  manual control in the UI. Both paths call the same domain function, so
  validation, safety checks and supersession are written once:

  | Chat | Shared function | Manual route |
  |---|---|---|
  | extraction `add`, `supersede`, `remove` | `memory/supersede.apply_operations` via `memory/manual_edit.py` | `POST`, `PATCH`, `DELETE /api/preferences` |
  | cart tools | `orders/cart_add.py`, `orders/cart_edit.py` | `/api/cart` routes |

- **One direction only.** Some actions are manual only on purpose. The chat
  never places an order; it proposes, and the guest's button places it
  (ADR 0019).
- **Enforced by a test.** `backend/tests/test_chat_parity.py` fails when:
  - a tool or a memory operation has no manual route;
  - the UI's `PreferenceKind` list misses a kind the chat can store. The
    frontend's `LABELS` record then needs a label per kind, and the page
    test checks each label has a section.
- **The Preferences page** (`/preferences`) edits every kind:
  - allergies and diet, marked "always enforced"; removing an allergy, or
    loosening or removing the diet, asks first;
  - spice, budget and the calorie goal;
  - likes and dislikes;
  - days you avoid and days you want;
  - the history of replaced facts.

  The allowed values come from `GET /api/preferences/vocabulary`, so the UI
  keeps no copy of them.
- **Day likes.** A new soft kind `day_like` (migration 0009) is stored like a
  day rule: "friday: fish". It is the opposite of `day_dislike` for the same
  food, so one replaces the other. On that weekday it works like a like, and
  matching dishes on the menu page get a "Today's pick for you" badge (chat
  cards are built without tastes, as for "You like this"). It never blocks.

## Alternatives considered
- **Make the memory panel editable inline.** It is less work, but the panel
  sits beside the chat on a restaurant page. A page of its own is easier to
  find and has room for every kind.
- **Separate write code for manual edits.** It would be simpler to start,
  but the two paths would drift. A manual edit could then skip a check the
  chat path has, or the other way round.
- **Parity as a written rule only.** It is easy to forget when the next tool
  is added. The test makes forgetting fail CI.

## Consequences
- A new chat tool or memory operation needs its manual route in the same
  change, or the parity test fails.
- A guest can remove their own allergy by hand. This is their data, so it is
  allowed, behind a confirmation. ADR 0016 still stops the *model* from
  removing one by mistake.
- Manual edits have no source message, so `source_message_id` is null.
