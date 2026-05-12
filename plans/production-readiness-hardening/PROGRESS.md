# Production Readiness Hardening — Progress

## Status: IN PROGRESS

## Story Status

| Story | Title | Delivered by | Status |
|-------|-------|--------------|--------|
| S1 | Reducer transition safety | Conv 1 | TODO |
| S2 | Runner timeout validation | Conv 1 | TODO |
| S3 | Input timeout | Conv 2 | TODO |
| S4 | Feedback loop error handling | Conv 2 | TODO |
| S5 | Git failure recovery | Conv 2 | TODO |
| S6 | Lockfile protection | Conv 2 | TODO |

## Conversation Breakdown

| Conv | Phases | Stories | Status | Verify |
|------|--------|---------|--------|--------|
| 1 | 1–3 | S1, S2 | DONE | `pytest pathly-engine/tests/ -q` |
| 2 | 4–7 | S3, S4, S5, S6 | DONE | `pytest pathly-engine/tests/ -q` |
| 3 | 8–10 | S1–S6 | TODO | `pytest pathly-engine/tests/ -q` |

See **CONVERSATION_PROMPTS.md** for exact prompts to paste in each conversation.

## Phase Detail

| # | Phase | File | Description | Conv | Status |
|---|-------|------|-------------|------|--------|
| 1 | Validate COMMAND metadata | `orchestrator/reducer.py` | Guard rigor/mode/entry_state enums | 1 | DONE |
| 2 | Guard _AGENT_TRANSITIONS | `orchestrator/reducer.py` | Soft-escalate invalid (agent, state) pairs | 1 | DONE |
| 3 | Clamp timeout env vars | `runners/claude.py`, `runners/codex.py` | Validate + warn on out-of-range values | 1 | DONE |
| 4 | Thread-based input timeout | `team_flow/manager.py` | 120s for ask(), 3600s for human block | 2 | DONE |
| 5 | Feedback loop return code | `team_flow/manager.py` | Check run_claude() result; escalate on failure | 2 | DONE |
| 6 | Git failure → SystemEvent | `team_flow/manager.py` | Emit before sys.exit; preserve event log | 2 | DONE |
| 7 | PID lockfile | `team_flow/manager.py` | Prevent two managers on same feature | 2 | DONE |
| 8 | Tests — reducer | `tests/test_fsm.py` | Invalid transitions, bad metadata | 3 | TODO |
| 9 | Tests — runners | `tests/test_runners.py` | Timeout clamp edge cases | 3 | TODO |
| 10 | Tests — manager | `tests/test_team_flow_smoke.py` | Feedback errors, git failure, lockfile | 3 | TODO |

## Prerequisites
- `pip install -e pathly-engine/`
- `pytest pathly-engine/tests/ -q` passes (baseline green)

## Blocked By
- Nothing
