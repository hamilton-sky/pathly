# split-team-flow-driver - Progress

## Status: NOT STARTED

## Story Status

| Story | Title | Delivered by | Status |
|-------|-------|--------------|--------|
| S1.1 | Agent execution is isolated | Conv 1 | TODO |
| S1.2 | Feedback routing is isolated | Conv 2 | TODO |
| S1.3 | Driver is a coordinator | Conv 3 | TODO |

## Conversation Breakdown

| Conv | Phases | Stories | Status | Verify |
|------|--------|---------|--------|--------|
| 1 | Phase 1 | S1.1 | TODO | `pytest -q` |
| 2 | Phase 2 | S1.2 | TODO | `pytest -q` |
| 3 | Phase 3 | S1.3 | TODO | `pytest -q` |

See **CONVERSATION_PROMPTS.md** for exact implementation prompts.

## Phase Detail

| # | Phase | Layer | Description | Conv | Status | Key Files |
|---|-------|-------|-------------|------|--------|-----------|
| 1 | Extract agent runner | Runtime orchestration | Move Claude subprocess execution and usage parsing out of Driver. | 1 | TODO | `orchestrator/agent_runner.py`, `scripts/team_flow.py` |
| 2 | Extract feedback helpers | File protocol | Move feedback scanning and priority selection into a focused helper. | 2 | TODO | `orchestrator/feedback.py`, `scripts/team_flow.py` |
| 3 | Slim Driver | Runtime orchestration | Make Driver coordinate collaborators while preserving behavior. | 3 | TODO | `scripts/team_flow.py` |

## Prerequisites
- `pytest -q` is green before Conversation 1 starts.
- Current hook/test self-repair changes are not mixed accidentally with the driver split.

## Blocked By
- Nothing.
