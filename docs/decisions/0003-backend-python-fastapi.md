# 0003: Backend with Python and FastAPI

- Status: Accepted
- Date: 2026-10-17

## Decision
Python 3.12 with FastAPI, Pydantic v2 and async SQLAlchemy.

## Why
- First-class OpenAI SDK and the strongest AI and eval tooling ecosystem.
- Async by default, which suits a workload that mostly waits on LLM calls.
- Pydantic validates every boundary: tool arguments, tool results and the
  model's structured answer. This is how grounding is enforced.
- Automatic OpenAPI docs at `/docs` help reviewers explore the API.

## Alternatives considered
- Node with TypeScript: one language across the stack, but weaker eval tooling.
- Agent frameworks (LangChain, LangGraph): more abstraction than a two-tool
  agent needs, and harder to explain line by line in the interview.

## Consequences
- We write the agent loop ourselves (about one file). Full control and full
  understanding, at the cost of building retries and limits by hand.
