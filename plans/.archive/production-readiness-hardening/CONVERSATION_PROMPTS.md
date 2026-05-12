# Production Readiness Hardening — Conversation Guide

Split into 3 conversations. Each produces runnable, tested code.
After each conversation, **commit your changes** before starting the next.

---

## Conversation 1: Reducer + Runner Hardening (Phases 1–3)

**Stories delivered:** S1 (reducer safety), S2 (timeout validation)

**Prompt to paste:**
```
Read plans/production-readiness-hardening/FEATURE_INDEX.md first to orient yourself and verify codebase paths.

Implement production-readiness-hardening Conversation 1 (Phases 1–3) from plans/production-readiness-hardening/IMPLEMENTATION_PLAN.md.

Scope:

Phase 1 — Validate COMMAND event metadata (reducer.py)
In the `if event.type == Events.COMMAND:` block, after reading rigor/mode/entry_state from
event.metadata, validate each against its valid set (Rigor.*, Mode.*, FSMState.*).
If any value is unrecognized or empty, set new_state.current = FSMState.BLOCKED_ON_HUMAN and return.
Valid values pass through unchanged. The reducer must remain a pure function with no I/O.

Phase 2 — Guard _AGENT_TRANSITIONS lookup (reducer.py)
In the `if event.type == Events.AGENT_DONE:` block, add an else branch to the
`if key in _AGENT_TRANSITIONS:` check. On miss: set new_state.current = FSMState.BLOCKED_ON_HUMAN.
No other changes to this block.

Phase 3 — Validate and clamp timeout env vars (runners/claude.py, runners/codex.py)
Add a module-level `_validated_timeout(raw, env_var)` helper that:
  - raises ValueError for non-numeric input (include env var name in message)
  - clamps to [60, 7200] with a stderr warning if out of range
  - returns the int unchanged if in range
Replace the bare `int(os.environ.get(...))` timeout read in ClaudeRunner.run() and
CodexRunner.run() with calls to _validated_timeout. See IMPLEMENTATION_PLAN.md Phase 3
for the exact env var precedence logic.

Do NOT touch team_flow/manager.py or any test files yet.

Verify: pytest pathly-engine/tests/ -q
After done, update plans/production-readiness-hardening/PROGRESS.md phases 1–3 to DONE
and mark Conversation 1 as DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** All existing tests pass. `reduce(state, COMMAND_event_with_bad_rigor)`
returns state with `current=BLOCKED_ON_HUMAN`. `ClaudeRunner.run()` with `CLAUDE_AGENT_TIMEOUT=0`
prints a warning and uses 60s.

**Files touched:** `pathly-engine/orchestrator/reducer.py`, `pathly-engine/runners/claude.py`, `pathly-engine/runners/codex.py`

---

## Conversation 2: Manager Hardening (Phases 4–7)

**Stories delivered:** S3 (input timeout), S4 (feedback loop errors), S5 (git failure), S6 (lockfile)

**Prompt to paste:**
```
Read plans/production-readiness-hardening/FEATURE_INDEX.md first to orient yourself and verify codebase paths.

Implement production-readiness-hardening Conversation 2 (Phases 4–7) from plans/production-readiness-hardening/IMPLEMENTATION_PLAN.md.

Scope — all changes are in team_flow/manager.py only:

Phase 4 — Thread-based input() timeout
Add a module-level `_timed_input(prompt, timeout) -> str | None` helper using threading.Thread
(daemon=True). Returns the user's input string, or None on timeout.
Replace ALL input() calls in ask(), _startup_verify(), and _handle_human_block() with _timed_input.
Timeout values: 120s for ask() and _startup_verify() prompts; 3600s for _handle_human_block().
On None return: print the timeout message (see IMPLEMENTATION_PLAN.md Phase 4 for exact text),
emit SystemEvent(action="TIMEOUT"), then sys.exit(0).
Do not use select.select() — it is not portable on Windows stdin.

Phase 5 — Check run_claude() return code in feedback loop
In _handle_feedback(), capture the return code from every run_claude() call.
On non-zero return code: call a new _escalate_feedback_error(active, rc) method that
logs the failure, writes HUMAN_QUESTIONS.md with details, emits FileCreatedEvent, and returns.
The feedback file must remain on disk. See IMPLEMENTATION_PLAN.md Phase 5 for the full method body.
Do not change _handle_review_failure() — it already has its own zero-diff escalation logic.

Phase 6 — Git failure → SystemEvent before exit
In _run_building_state(), wrap the subprocess.run() git status call in try/except.
Catch subprocess.TimeoutExpired, FileNotFoundError, and OSError.
On any exception: emit SystemEvent(action="ERROR", metadata={"error": str(exc)}), then sys.exit(1).
If git succeeds but tree is dirty: emit SystemEvent(action="ERROR", metadata={"error": "working tree not clean"}), then sys.exit(1).
The emit() must happen before sys.exit() in all branches.

Phase 7 — PID lockfile
Add module-level helpers: _lock_path(plan_dir), _acquire_lock(plan_dir, feature), _release_lock(plan_dir).
See IMPLEMENTATION_PLAN.md Phase 7 for full implementation including stale-PID detection via os.kill(pid, 0).
In TeamFlowDriver.__init__, after self.plan_dir is assigned:
  _acquire_lock(self.plan_dir, self.feature)
  atexit.register(_release_lock, self.plan_dir)
Import atexit at the top of the file.

Do NOT touch reducer.py, runners/, or test files.

Verify: pytest pathly-engine/tests/ -q
After done, update plans/production-readiness-hardening/PROGRESS.md phases 4–7 to DONE
and mark Conversation 2 as DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** All existing tests pass. `_timed_input` helper exists and is used everywhere
`input()` was called. `_escalate_feedback_error` exists. `_acquire_lock` / `_release_lock` exist.
`plans/<feature>/.lock` is created on driver start and removed on exit.

**Files touched:** `pathly-engine/team_flow/manager.py`

---

## Conversation 3: Tests for All Gaps (Phases 8–10)

**Stories delivered:** S1–S6 (test coverage for all hardening changes)

**Prompt to paste:**
```
Read plans/production-readiness-hardening/FEATURE_INDEX.md first to orient yourself and verify codebase paths.

Implement production-readiness-hardening Conversation 3 (Phases 8–10) from plans/production-readiness-hardening/IMPLEMENTATION_PLAN.md.

Conversations 1 and 2 are complete. Add tests that cover the new behavior. Do not modify any
production code — only test files.

Phase 8 — Tests for reducer hardening (test_fsm.py)
Add to the existing test_fsm.py file:
- test_invalid_agent_state_pair_escalates: AGENT_DONE(agent=Agent.BUILDER) while state=IDLE
  → result state is BLOCKED_ON_HUMAN
- test_valid_agent_state_pair_unaffected: AGENT_DONE(agent=Agent.BUILDER, state=BUILDING)
  → result state is REVIEWING (existing behavior preserved)
- test_command_bad_rigor_escalates: COMMAND event with rigor="garbage" → BLOCKED_ON_HUMAN
- test_command_bad_mode_escalates: COMMAND event with mode="garbage" → BLOCKED_ON_HUMAN
- test_command_bad_entry_state_escalates: COMMAND event with entry_state="INVALID_STATE" → BLOCKED_ON_HUMAN
- test_command_valid_metadata_passes_through: COMMAND with rigor=Rigor.LITE, mode=Mode.FAST,
  entry_state=FSMState.STORMING → state.current == FSMState.STORMING

Phase 9 — Tests for runner timeout validation (test_runners.py)
Add to the existing test_runners.py file:
- test_timeout_zero_clamped_to_min: CLAUDE_AGENT_TIMEOUT=0 → timeout used is 60, stderr contains "[WARNING]"
- test_timeout_negative_clamped_to_min: CLAUDE_AGENT_TIMEOUT=-100 → clamped to 60 with warning
- test_timeout_above_max_clamped: CLAUDE_AGENT_TIMEOUT=99999 → clamped to 7200 with warning
- test_timeout_valid_unchanged: CLAUDE_AGENT_TIMEOUT=600 → timeout used is 600, no warning
- test_timeout_non_numeric_raises: CLAUDE_AGENT_TIMEOUT="fast" → ValueError raised
- test_codex_timeout_clamped: PATHLY_RUNNER_TIMEOUT=0 → clamped to 60 in CodexRunner

Phase 10 — Tests for manager hardening (test_team_flow_smoke.py)
Add to the existing test_team_flow_smoke.py file:
- test_feedback_agent_failure_escalates: run_claude returns 1 during _handle_feedback
  → HUMAN_QUESTIONS.md created, SystemEvent ERROR emitted, feedback file still on disk
- test_git_failure_emits_system_event: git status raises FileNotFoundError in _run_building_state
  → SystemEvent(action="ERROR") is emitted before process exits
- test_lockfile_created_on_start: TeamFlowDriver initializes → plans/<feature>/.lock exists with driver PID
- test_lockfile_prevents_second_instance: two drivers for same feature → second raises SystemExit
- test_stale_lockfile_cleared: lockfile with dead PID → warning printed, driver starts normally

Use monkeypatch and tmp_path fixtures (already used in the test file). Do not add external test deps.
Keep each test focused and under 20 lines.

Verify: pytest pathly-engine/tests/ -q
After done, update plans/production-readiness-hardening/PROGRESS.md phases 8–10 to DONE,
mark Conversation 3 as DONE, and set overall Status to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** All new tests pass alongside all existing tests. No regressions.

**Files touched:** `pathly-engine/tests/test_fsm.py`, `pathly-engine/tests/test_runners.py`, `pathly-engine/tests/test_team_flow_smoke.py`
