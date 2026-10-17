# 0016: A `removed` status, and checked targets for memory changes

- Status: Accepted
- Date: 2026-10-17
- Amends: [0011](0011-structured-memory-with-supersession.md)

## Context
ADR 0011 gives preferences two statuses, active and superseded. Some facts
stop being true with nothing replacing them ("actually I eat fish now" ends a
vegetarian diet). Review also showed that a wrong `target_id` from extraction
could remove or replace an unrelated fact, such as a stored allergy, which
would switch off a hard constraint.

## Decision
- Preferences have three statuses: active, superseded (with `superseded_by`)
  and removed.
- A `remove` must name the target's kind, and its value too unless the kind
  allows only one active row (diet, budget, spice).
- A `supersede` must keep the target's kind, or switch between like and
  dislike of the same thing.
- An operation whose target is missing, inactive, owned by another user or
  does not match is dropped and logged.

## Consequences
- History still shows every change; removed rows stay for audit.
- A rare honest correction phrased against the wrong kind is dropped instead
  of applied. The user can say it again; losing an allergy silently is worse.
