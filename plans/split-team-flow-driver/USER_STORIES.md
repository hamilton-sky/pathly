# split-team-flow-driver - User Stories

## Context

`scripts/team_flow.py` currently owns orchestration, subprocess execution,
feedback routing, prompt construction, git checks, startup integrity checks,
and logging in one `Driver` class. The code works, but the class is too large
for production hardening: small changes to hook behavior, retry policy, agent
execution, or FSM persistence all land in the same file.

This feature extracts focused runtime modules while preserving the public
workflow behavior and the existing CLI contract. The goal is not to redesign
the FSM. The goal is to make the existing FSM driver easier to test, review,
and adapt for Codex/Claude host differences.

## Stories

### Story 1.1: Agent execution is isolated
**As a** Pathly maintainer, **I want** subprocess-based agent execution in a
focused module, **so that** timeouts, output parsing, and host-specific runner
behavior can be tested without exercising the full pipeline driver.

**Acceptance Criteria:**
- [ ] A focused agent runner module owns `claude -p` invocation and usage parsing.
- [ ] The runner preserves the current timeout behavior using `CLAUDE_AGENT_TIMEOUT`.
- [ ] Existing `Driver.run_claude(...)` behavior remains available through a thin wrapper or injected runner.
- [ ] Existing tests still pass.

**Edge Cases:**
- Timeout returns a non-zero result and emits/logs the same timeout behavior as today.
- Non-JSON Claude output still produces an empty usage dict.

**Delivered by:** Phase 1 -> Conversation 1

### Story 1.2: Feedback routing is isolated
**As a** Pathly maintainer, **I want** feedback-file priority and routing helpers
outside the monolithic driver, **so that** file protocol changes can be tested
without running agent subprocesses.

**Acceptance Criteria:**
- [ ] Feedback priority order remains unchanged.
- [ ] Open-feedback discovery is owned by a focused helper/module.
- [ ] The driver still routes `HUMAN_QUESTIONS.md`, architecture feedback,
  design questions, implementation questions, review failures, and test failures
  exactly as before.
- [ ] Existing tests still pass.

**Edge Cases:**
- Missing `feedback/` directory returns no open files.
- Unknown markdown files in `feedback/` do not outrank known feedback files.

**Delivered by:** Phase 2 -> Conversation 2

### Story 1.3: Driver is a coordinator, not the owner of every policy
**As a** Pathly maintainer, **I want** `Driver` to coordinate the workflow using
small collaborators, **so that** future Codex compatibility and production
hardening do not require editing one high-risk class.

**Acceptance Criteria:**
- [ ] `scripts/team_flow.py` remains a working executable entrypoint.
- [ ] `Driver` keeps the main state loop but delegates agent running and
  feedback utilities to focused modules.
- [ ] Tests cover the extracted modules directly.
- [ ] `pytest -q` passes.

**Edge Cases:**
- `pathly flow <feature>` continues to set `team_flow.REPO_ROOT` correctly.
- Existing event log and state reconstruction behavior is unchanged.

**Delivered by:** Phase 3 -> Conversation 3
