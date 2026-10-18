# 0023: A staff role for the restaurant CRM

- Status: Accepted, not built (phase 16 was cut for the deadline, 2026-10-18)
- Date: 2026-10-17
- Extends: 0013 (identity)

## Context
The restaurant CRM shows orders and trends across all guests. Guests must
never see it. v1 has no roles.

## Decision
- `users.role` is `guest` or `staff`. New logins are always guests. Staff
  accounts are created only by the seed script; the demo one is `demo_staff`.
- Every CRM route depends on `require_staff`, which reads the role from the
  database for the session user. A wrong role returns 403.
- Staff see aggregates, and orders by username. A segment ("vegetarians
  order...") is shown only when it has 5 or more guests.

## Alternatives considered
- A separate admin app or password: a second login system to maintain.
- A list of staff usernames in settings: no migration, but the role would
  not be visible in the data model.

## Consequences
- Still demo-grade identity (username and PIN), now with a privileged
  account whose PIN is public. The CRM is read-only, so the worst case is
  someone viewing simulated and demo data.
