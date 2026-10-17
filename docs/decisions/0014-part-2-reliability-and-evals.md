# 0014: Part 2 challenge: reliability and evaluation

- Status: Accepted
- Date: 2026-10-17

## Problem
An ordering assistant that remembers users can fail quietly: recommend an item
with a stored allergen, invent a price, forget a correction, or mix two users'
memory. Demos hide these failures. Without measurement, "it works" is a claim.

## Why this over other directions
- It protects the baseline's core promises: safety, grounding and memory.
- The brief values demonstrated results over claims; evals are the evidence.
- Voice, integrations and scale add surface area without proving the core works.

## Scope
- Eval suite with categories: allergen safety, diet compliance, grounding,
  memory recall, preference updates, isolation, extraction precision.
- Deterministic graders wherever possible; LLM judge only where needed.
- Results per category, several runs per case, worst run reported for safety.
- One full loop: measure, find failures, fix, measure again.

## Left out
- Production observability (tracing dashboards, alerting).
- Load and latency testing.
- Automatic prompt optimization.

## Validation
`docs/eval-report.md` with before and after results on the same cases and model.

## Outcome
42 cases, 3 runs each, on gpt-6-luna (`docs/eval-report.md`). The safety
categories passed every run from the start. The evals found memory changing
silently, with no confirmation to the user (preference_update 4/6). Two
fixes to a memory-change note brought it to 6/6, but a code review found they
shortened replies (dead ends 18 to 43). A third fix kept the confirmation and
brought dead ends to 11, with every graded check still passing.
