# split-team-flow-driver - Conversation Guide

Split into 3 conversations. Each conversation must keep behavior stable and end
with `pytest -q` passing.

---

## Conversation 1: Extract agent runner (Phase 1)

**Stories delivered:** S1.1
**Depends on:** Baseline `pytest -q` is green before starting.

**Prompt to use:**
```text
Implement split-team-flow-driver Conversation 1 from
plans/split-team-flow-driver/IMPLEMENTATION_PLAN.md.

Scope:
- Create `orchestrator/agent_runner.py`.
- Move Claude subprocess execution and usage parsing out of `scripts/team_flow.py`.
- Preserve the current `Driver.run_claude(prompt) -> (returncode, usage)` behavior.
- Preserve `CLAUDE_AGENT_TIMEOUT`, default `1800`.
- Add focused tests for usage parsing and timeout handling.

Do NOT:
- Change FSM transitions.
- Change event schemas.
- Change public CLI commands.
- Move feedback routing yet.

Verify: `pytest -q`
After done, update `plans/split-team-flow-driver/PROGRESS.md` Conv 1 to DONE.
```

**Expected output:** `Driver` delegates agent execution; tests cover the runner.
**Files touched:** `orchestrator/agent_runner.py`, `scripts/team_flow.py`, tests.

---

## Conversation 2: Extract feedback helpers (Phase 2)

**Stories delivered:** S1.2
**Depends on:** Conversation 1 is DONE and runner extraction tests pass.

**Prompt to use:**
```text
Implement split-team-flow-driver Conversation 2 from
plans/split-team-flow-driver/IMPLEMENTATION_PLAN.md.

Scope:
- Create `orchestrator/feedback.py`.
- Move feedback priority and open-feedback discovery helpers out of `scripts/team_flow.py`.
- Preserve the exact priority order:
  HUMAN_QUESTIONS.md, ARCH_FEEDBACK.md, DESIGN_QUESTIONS.md,
  IMPL_QUESTIONS.md, REVIEW_FAILURES.md, TEST_FAILURES.md.
- Add focused tests for missing feedback directory, known file priority, and unknown md files.

Do NOT:
- Change hook behavior.
- Change feedback file names.
- Move agent prompt builders yet.

Verify: `pytest -q`
After done, update `plans/split-team-flow-driver/PROGRESS.md` Conv 2 to DONE.
```

**Expected output:** feedback file policy is testable outside `Driver`.
**Files touched:** `orchestrator/feedback.py`, `scripts/team_flow.py`, tests.

---

## Conversation 3: Slim Driver around collaborators (Phase 3)

**Stories delivered:** S1.3
**Depends on:** Conversations 1 and 2 are DONE, so both extracted collaborators exist.

**Prompt to use:**
```text
Implement split-team-flow-driver Conversation 3 from
plans/split-team-flow-driver/IMPLEMENTATION_PLAN.md.

Scope:
- Keep `scripts/team_flow.py` executable.
- Keep `Driver.run()` as the main workflow loop.
- Replace remaining direct runner/feedback utility code with calls to the extracted modules.
- Add or update smoke tests only where behavior is covered poorly.

Do NOT:
- Introduce broad inheritance hierarchies.
- Rewrite the reducer/event-log FSM.
- Change the `pathly flow` CLI contract.
- Move prompt builders unless it is necessary to complete this conversation safely.

Verify: `pytest -q`
After done, update `plans/split-team-flow-driver/PROGRESS.md` Conv 3 to DONE.
```

**Expected output:** `Driver` is smaller and acts mainly as coordinator.
**Files touched:** `scripts/team_flow.py`, tests as needed.
