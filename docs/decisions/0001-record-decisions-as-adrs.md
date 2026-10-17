# 0001: Record decisions as ADRs

- Status: Accepted
- Date: 2026-10-17

## Context
The technical interview is built on our decisions. Reviewers explore the repo
alone, and an AI coding agent works on it across many sessions. Decisions that
live only in chat are lost.

## Decision
Each significant decision gets a short ADR in `docs/decisions/`, numbered in
order. ADRs are not edited after acceptance; a new ADR supersedes an old one
and both are updated to link each other.

## Consequences
- Reviewers can read the reasoning before the interview.
- Claude Code can check decisions before changing something.
- Small overhead per decision. Only significant ones get an ADR.
