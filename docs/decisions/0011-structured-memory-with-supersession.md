# 0011: Structured memory with supersession

- Status: Accepted, amended by [0016](0016-removed-status-and-target-checks.md)
- Date: 2026-10-17

## Context
Memory must survive across conversations, influence recommendations, and adapt
when users change their mind. Facts must be replaced, not stacked.

## Decision
- Preferences are typed rows (`kind`: allergy, diet, dislike, like, budget,
  spice) with `status` active or superseded and a link to what replaced them.
- After each user message, an extraction call returns validated operations
  (`add`, `supersede`, `remove`) against the current profile. It runs before
  the reply so the answer uses the updated profile.
- The active profile is injected at the top of the context on every turn.
  It is never summarized.
- Few-shot examples teach what not to store ("my friend is vegan").

## Alternatives considered
- Full chat history as memory: grows without limit, facts get lost in the
  middle, and there is no clean way to replace an old fact.
- Let the chat model call a `remember` tool: one call fewer, but it is easy to
  skip, and extraction is harder to test on its own.
- Vector memory: built for fuzzy recall over large text; overkill here.

## Consequences
- Two LLM calls per turn: more latency and cost, accepted for reliability.
- Superseded rows keep history, so changes are auditable and demoable.
