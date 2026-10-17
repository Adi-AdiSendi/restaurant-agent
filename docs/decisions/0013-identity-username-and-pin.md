# 0013: Identity by username and PIN

- Status: Accepted
- Date: 2026-10-17

## Context
The brief needs returning users to be identified and isolated, and lets us
choose how. Reviewers must be able to test it in seconds.

## Decision
Username plus a 4-digit PIN. The PIN is hashed (argon2). A signed, HTTP-only
session cookie carries the user ID. New usernames register on first login.
Two demo accounts are documented in the README.

## Alternatives considered
- Name only: fastest, but anyone can open anyone's memory, which undermines
  the isolation requirement.
- Email and password or OAuth: real auth, but setup cost with no benefit
  for the brief.

## Consequences
- Not production authentication. Listed as a limitation.
