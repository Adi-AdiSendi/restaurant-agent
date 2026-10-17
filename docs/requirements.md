# Requirements traceability

Every requirement from the brief, where it is implemented, and how it is
verified. Update the last two columns as phases finish.

## Part 1: Baseline
| # | Requirement (brief section) | Implemented in | Verified by |
|---|---|---|---|
| R1 | Natural conversation gathers preferences, no questionnaire (2.1) | `agent/`, `memory/extract.py` | `tests/memory/test_extract.py`; evals: extraction_precision |
| R2 | Recommendations consider preferences, restrictions, request (2.2) | `agent/`, `tools/search_menu.py`, `menu/constraints.py`, `safety/` | `tests/tools/test_search_menu.py`, `tests/safety/test_guard.py`, `tests/agent/test_loop_safety.py`; evals: diet_compliance, allergen_safety |
| R3 | Grounded in real menu data, nothing invented (2.2) | ID-only answer, `agent/grounding.py`, `safety/`, DB cards | `tests/agent/test_loop.py`; evals: grounding |
| R4 | Memory persists across independent conversations (2.3) | `memory/supersede.py`, `preferences` table | `tests/api/test_memory_flow.py`; evals: memory_recall |
| R5 | Memory meaningfully changes recommendations (2.3) | profile block in `agent/context.py` | `tests/agent/test_context.py`, `tests/api/test_memory_flow.py`; evals: memory_recall |
| R6 | Corrections and changes replace old facts (2.4) | `memory/supersede.py` | `tests/memory/test_supersede.py`, `tests/api/test_memory_flow.py`; evals: preference_update |
| R7 | Returning users identified (2.5) | `users/`, username + PIN, signed cookie | `tests/users/test_service.py`, `tests/api/test_auth.py` |
| R8 | Users' memories isolated (2.5) | `user_id` from session only (`api/deps.py`), queries scoped by it | `tests/api/test_memory_flow.py`, `tests/memory/test_supersede.py`; evals: isolation |
| R9 | Deployed, usable interface (2.6) | `frontend/` on Netlify, backend on Render free (`netlify.toml`, `render.yaml`, ADR 0017) | frontend tests incl. startup gate; live checks in phase 6 |

## Menu (section 3)
| # | Requirement | Verified by |
|---|---|---|
| M1 | 12+ items across 3+ categories | `tests/menu/test_seed_data.py` (18 items, 4 categories) |
| M2 | Different prices | `tests/menu/test_seed_data.py` (all distinct, 16 to 85 SAR) |
| M3 | Vegetarian and non-vegetarian | `tests/menu/test_seed_data.py` (12 veg, 7 vegan, 6 non-veg) |
| M4 | Different spice levels | `tests/menu/test_seed_data.py` (0 to 3 all used) |
| M5 | Explicit ingredients and allergens | `tests/menu/test_seed_data.py`, non-null columns + CHECK on vocabulary (`tests/menu/test_constraints.py`) |
| M6 | Overlapping items for comparison and conflicts | documented in `backend/data/README.md` |

## Part 2: Challenge (section 4)
| # | The brief asks | Answered in |
|---|---|---|
| C1 | Problem identification | ADR 0014, README, video |
| C2 | Prioritization | ADR 0014, video |
| C3 | Scope and trade-offs, what was left out | ADR 0014, README limitations |
| C4 | Execution and validation | `backend/evals/`, `docs/eval-report.md` |

## Deliverables (section 6)
| # | Deliverable | Status |
|---|---|---|
| D1 | Live URL, available through evaluation, test instructions | in progress: config done, live URL after the phase 6 spike; keep-awake ping; demo accounts in README |
| D2 | Repo with README: local run, architecture, decisions, setup, limitations | not started |
| D3 | No secrets committed | CI secret scan |
| D4 | Video 8 to 12 min: baseline demo, challenge, deep dive, trade-offs, results | not started |
| D5 | Google Drive folder with URL, repo, video, access notes | not started |
