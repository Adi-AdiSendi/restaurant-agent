# 0008: Feature-based folders and one-way dependencies

- Status: Accepted
- Date: 2026-10-17

## Context
Reviewers explore the source alone. They will ask "where is memory?" not
"where are the services?". The line limit (ADR 0007) creates many small files,
so the structure must carry the navigation.

## Decision
- Folders are named after product parts: agent, tools, menu, memory, safety,
  users, api, db. No `utils`, `helpers` or `common` folders.
- Each top-level folder has a short README: purpose, entry point, dependencies.
- Dependencies point one way:
  `api -> agent -> tools | memory | safety -> menu | users -> db`.
  Enforced with import-linter in CI.

## Alternatives considered
- Layer folders (routes, services, repositories): familiar, but scatters one
  feature across many folders and adds a repository layer we do not need.

## Consequences
- The architecture diagram cannot drift from the code without CI failing.
