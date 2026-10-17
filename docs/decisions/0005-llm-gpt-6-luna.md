# 0005: OpenAI GPT-6 Luna through the Responses API

- Status: Accepted
- Date: 2026-10-17

## Decision
Use OpenAI GPT-6 Luna (released 2026-09-22) through the Responses API, for both
the chat agent and the preference extraction pass. The model ID is a setting
(`OPENAI_MODEL`), not a constant.

## Why
- Low latency, suited to chat and lightweight agentic work.
- Supports tool calling and structured outputs, which grounding depends on.
- Low cost (about $0.10 input and $0.50 output per 1M tokens at decision time),
  so the eval suite can run many times.

## Alternatives considered
- GPT-6.1 Sol: stronger reasoning at higher cost. Kept as the fallback if evals
  show Luna failing on multi-constraint reasoning. Switching is a config change.
- Claude models: strong at tool use, but the stack is already set on OpenAI and
  a single provider keeps the scope small.

## Consequences
- Output varies between runs, so evals run each case several times.
- One provider dependency. An outage takes the agent down; handled with a
  clear error message, not a second provider.
