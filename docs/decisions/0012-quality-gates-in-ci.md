# 0012: Quality gates in pre-commit and CI

- Status: Accepted
- Date: 2026-10-17

## Decision
Every commit and pull request runs:
- Python: ruff (lint and format), pyright strict, pytest.
- Frontend: ESLint, Prettier, TypeScript strict, Vitest.
- Repo: line limits, import-linter, secret scan.
Dependencies are locked (`uv.lock`, `package-lock.json`).

## Why
- Clean code and low debt are enforced by tools, not by taste or memory.
- CLAUDE.md is advisory; CI is not. Rules that can be checked are checked.
- A green pipeline is quick, visible evidence for reviewers.

## Consequences
- Some setup time in phase 0, paid back on every later change.
