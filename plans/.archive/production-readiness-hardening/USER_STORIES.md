# Production Readiness Hardening — User Stories

## Context

Seven critical gaps were found during a production-readiness exploration of `pathly-engine`.
The FSM architecture is sound, but these gaps can cause silent state corruption, indefinite
hangs, or processes exiting without recording errors. This hardening closes all seven.

---

## Stories

### Story 1: Reducer transition safety (gaps 1 + 4)

**As a** pathly operator, **I want** the FSM to reject invalid transitions gracefully,
**so that** no bad event can silently corrupt the pipeline state.

**Acceptance Criteria:**
- [ ] An `AGENT_DONE` event for an `(agent, state)` pair not in `_AGENT_TRANSITIONS` escalates to `BLOCKED_ON_HUMAN` instead of returning unchanged state
- [ ] A `COMMAND` event with an unrecognized `rigor` value escalates to `BLOCKED_ON_HUMAN`
- [ ] A `COMMAND` event with an unrecognized `mode` value escalates to `BLOCKED_ON_HUMAN`
- [ ] A `COMMAND` event with an unrecognized `entry_state` value escalates to `BLOCKED_ON_HUMAN`
- [ ] Valid transitions and metadata continue to work exactly as before

**Edge Cases:**
- Empty string values for rigor/mode/entry_state (treat as unrecognized)
- `AGENT_DONE` from a known agent but wrong state (e.g., builder DONE while IDLE)

**Delivered by:** Phase 1–2 → Conversation 1

---

### Story 2: Runner timeout validation (gap 2)

**As a** pathly operator, **I want** invalid timeout env var values to be rejected loudly,
**so that** a misconfigured timeout doesn't silently kill every agent call.

**Acceptance Criteria:**
- [ ] `CLAUDE_AGENT_TIMEOUT=0` is clamped to 60 with a stderr warning
- [ ] `CLAUDE_AGENT_TIMEOUT=-1` is clamped to 60 with a stderr warning
- [ ] `CLAUDE_AGENT_TIMEOUT=99999` is clamped to 7200 with a stderr warning
- [ ] `PATHLY_RUNNER_TIMEOUT` applies the same clamp logic in `CodexRunner`
- [ ] A valid value (e.g., `600`) passes through unchanged and no warning is emitted
- [ ] A non-numeric value raises a clear `ValueError` with the env var name in the message

**Edge Cases:**
- Both `CLAUDE_AGENT_TIMEOUT` and `PATHLY_RUNNER_TIMEOUT` set; `ClaudeRunner` uses `CLAUDE_AGENT_TIMEOUT` first
- Non-numeric string (e.g., `"fast"`) should raise, not silently use default

**Delivered by:** Phase 3 → Conversation 1

---

### Story 3: Input timeout (gap 3)

**As a** pathly operator running in a CI or non-interactive environment, **I want** `input()` calls to time out instead of blocking forever, **so that** the process always exits cleanly.

**Acceptance Criteria:**
- [ ] `ask()` pause prompts time out after 120s with a `SystemEvent(action="TIMEOUT")` emitted and a clean exit
- [ ] `_handle_human_block()` input times out after 3600s with a clean exit
- [ ] Timeout implementation is thread-based (compatible with Windows; no `select.select()` on stdin)
- [ ] On timeout, a clear message is printed: `[TIMEOUT] No response after Ns. Exiting — state preserved, resume with /pathly go <feature>.`

**Edge Cases:**
- User types partial input before timeout
- Process is running in a pipe (non-TTY stdin)

**Delivered by:** Phase 4 → Conversation 2

---

### Story 4: Feedback loop error handling (gap 5)

**As a** pathly operator, **I want** agent failures inside the feedback resolution loop to escalate to `BLOCKED_ON_HUMAN`, **so that** the pipeline never silently advances on a failed fix.

**Acceptance Criteria:**
- [ ] `run_claude()` returning non-zero inside `_handle_feedback()` emits `SystemEvent(action="ERROR")` and stops the loop
- [ ] The human is shown a clear message: which feedback file was being resolved and what the exit code was
- [ ] The feedback file remains on disk (not deleted) when the agent fails
- [ ] Successful agent calls (return code 0) are unaffected

**Edge Cases:**
- Agent returns non-zero but feedback file was deleted anyway (check disk state, not return code alone)
- `run_claude()` raises an exception rather than returning non-zero

**Delivered by:** Phase 5 → Conversation 2

---

### Story 5: Git failure recovery (gap 7)

**As a** pathly operator, **I want** git command failures to be recorded in the event log, **so that** the pipeline exits cleanly instead of dying with `sys.exit(1)` before any event is written.

**Acceptance Criteria:**
- [ ] `subprocess.CalledProcessError` from `git status` in `_run_building_state()` emits `SystemEvent(action="ERROR")` before exiting
- [ ] The error message (stderr from git) is included in the SystemEvent metadata
- [ ] The process exits after emitting the event (state is saved); it does not loop
- [ ] Normal git operation (clean working tree) is unaffected

**Edge Cases:**
- Git not installed at all (`FileNotFoundError`)
- Git timeout (`subprocess.TimeoutExpired`)

**Delivered by:** Phase 6 → Conversation 2

---

### Story 6: Lockfile protection (gap 6)

**As a** pathly operator, **I want** a second `team-flow` process for the same feature to be blocked at startup, **so that** two managers never write to the same `EVENTS.jsonl` simultaneously.

**Acceptance Criteria:**
- [ ] Starting a second driver for the same feature while one is already running prints: `[ERROR] production-readiness-hardening is already running (PID 1234). Stop it before starting a new one.` and exits with code 1
- [ ] A stale lockfile (PID of dead process) is detected, deleted, and startup continues normally with a logged warning
- [ ] The lockfile is always deleted on clean exit (normal, user quit, or `sys.exit`)
- [ ] The lockfile is always deleted on unclean exit (exception, signal) via `atexit` or `try/finally`
- [ ] Lockfile path: `plans/<feature>/.lock`

**Edge Cases:**
- PID in lockfile belongs to a different kind of process (reused PID after crash) — treat as stale if process name doesn't match
- Lockfile directory doesn't exist yet (first run)

**Delivered by:** Phase 7 → Conversation 2
