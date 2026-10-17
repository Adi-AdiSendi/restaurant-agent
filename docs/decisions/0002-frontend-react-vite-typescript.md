# 0002: Frontend with React, Vite and TypeScript

- Status: Accepted
- Date: 2026-10-17

## Context
The brief needs a usable deployed interface; a simple chat is enough. Effort
should go to the agent, not the UI.

## Decision
React with Vite and strict TypeScript, built to static files and served by
FastAPI from the same service.

## Why
- Large ecosystem of chat and UI patterns, so the interface takes hours, not days.
- Strict types catch payload mismatches with the backend early.
- Static build served by FastAPI means one service, one URL, and no CORS setup.
- Room to grow if Part 2 ever moves toward user experience.

## Alternatives considered
- Streamlit or Gradio: fastest, but limited control over layout and item cards.
- Next.js: adds a Node server and server rendering we do not need.

## Consequences
- Two toolchains (Python and Node) in one repo.
- Not cross-platform native; a mobile app would need React Native or similar.
