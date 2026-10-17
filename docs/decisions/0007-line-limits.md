# 0007: 100-line limit for code and agent instruction files

- Status: Accepted
- Date: 2026-10-17

## Decision
- CLAUDE.md, `.claude/rules/*.md` and `.claude/agents/*.md`: at most 100 lines.
- Source files: at most 100 lines. Tests: at most 150.
- Exempt: migrations, lockfiles, seed data, generated code.
- Enforced by `scripts/check_line_limits.py` in pre-commit and CI.

## Why
- Anthropic's documented target for CLAUDE.md is under 200 lines, since longer
  files use more context and reduce adherence. We chose 100 to keep
  instructions sharp and leave context for the work.
- Extra detail goes in path-scoped rules or in docs referenced by plain path.
  `@imports` are avoided because imported files load at launch and save no context.
- Small source files are readable for reviewers, force one responsibility per
  file, and let the coding agent read and edit precisely.

## Consequences
- More files and more navigation, so the folder structure must be obvious
  (ADR 0008).
- Some cohesive logic gets split. Split by responsibility, never mid-function.
