# split-team-flow-driver - Implementation Plan

## Overview

Refactor the Python team-flow runtime in small steps. Keep behavior stable and
avoid changing the core FSM reducer, event schema, CLI contract, or public
Pathly skill prompts. This plan starts after the current test suite is green.

## Phases

### Phase 1: Extract agent runner
**Layer:** Runtime orchestration
**Delivers stories:** S1.1
**Depends on:** Baseline `pytest -q` is green before starting.
**Files:**
- `orchestrator/agent_runner.py` - new focused runner for Claude subprocess calls.
- `scripts/team_flow.py` - keep `Driver.run_claude(...)` as a thin wrapper.
- `tests/test_agent_runner.py` - unit tests for timeout, return code, and usage parsing.

**Details:**
- Move subprocess invocation and `_parse_usage` behavior out of `Driver`.
- Preserve command shape:
  `claude -p <prompt> --allowedTools <tools> --output-format json`
- Preserve timeout source: `CLAUDE_AGENT_TIMEOUT`, default `1800`.
- Return the same shape currently used by the driver: `(returncode, usage_dict)`.
- Do not change state transitions in this phase.

**Verify:** `pytest -q`

### Phase 2: Extract feedback protocol helpers
**Layer:** Runtime orchestration / file protocol
**Delivers stories:** S1.2
**Depends on:** Phase 1 is complete and runner extraction tests pass.
**Files:**
- `orchestrator/feedback.py` - new helpers for feedback file scanning, priority selection, and TTL parsing if needed.
- `scripts/team_flow.py` - delegate feedback scanning and priority logic.
- `tests/test_feedback.py` - unit tests for priority and missing directory behavior.

**Details:**
- Move `FEEDBACK_PRIORITY` and feedback-file discovery logic into the new helper.
- Preserve priority order:
  `HUMAN_QUESTIONS.md`, `ARCH_FEEDBACK.md`, `DESIGN_QUESTIONS.md`,
  `IMPL_QUESTIONS.md`, `REVIEW_FAILURES.md`, `TEST_FAILURES.md`.
- Keep routing prompts in `Driver` for now; only extract file/protocol helpers.
- Do not alter hook behavior in this phase.

**Verify:** `pytest -q`

### Phase 3: Slim the driver around collaborators
**Layer:** Runtime orchestration
**Delivers stories:** S1.3
**Depends on:** Phases 1 and 2 are complete, so the driver can delegate to both extracted collaborators.
**Files:**
- `scripts/team_flow.py` - simplify `Driver` by using `AgentRunner` and feedback helpers consistently.
- `tests/test_team_flow_smoke.py` - update or extend smoke tests only where needed.
- Existing tests as needed.

**Details:**
- Keep the main `Driver.run()` state loop in place.
- Keep `scripts/team_flow.py` executable and compatible with `pathly flow`.
- Avoid moving prompt builders until runner and feedback extraction are stable.
- Do not introduce a broad framework or abstract base classes unless tests show a concrete need.

**Verify:** `pytest -q`

## Prerequisites
- Current self-repair changes should be committed or intentionally kept separate.
- Baseline must be green: `pytest -q`.

## Key Decisions
- Preserve the pure reducer/event-log FSM; do not rewrite it.
- Prefer small modules with direct functions/classes over a large inheritance model.
- Extract behavior in testable slices: runner first, feedback helpers second, driver slimming third.
- Keep `scripts/team_flow.py` as the public executable script for now.
