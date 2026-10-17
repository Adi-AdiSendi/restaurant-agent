# 0020: Tools get their context from the server

- Status: Accepted
- Date: 2026-10-17
- Amends: the tool handler shape in `.claude/rules/backend.md`

## Context
v1 tool handlers take `(session, arguments, hard_constraints)`. Cart tools
also need the user, the conversation and the restaurant. Rule 4 says the user
ID must come from the session, never from the model.

## Decision
Every handler takes `(arguments, context)`. `ToolContext` is built by the
server for each turn and holds the DB session, user ID, conversation ID,
restaurant ID and hard constraints. Tool schemas never contain any of these.
Read-only tools ignore what they do not need.

## Alternatives considered
- Add parameters to the handler one at a time: every new need changes every
  tool.
- Let the model pass the restaurant: it is not a secret, but scoping must not
  depend on the model getting it right.

## Consequences
- A tool cannot reach another user's cart or another restaurant's menu by
  its arguments.
- Tests build a `ToolContext` directly, which keeps them simple.
