# engine-hardening — User Stories

## S1 · `is_available()` timeout
**As a** pipeline operator,
**I want** `ClaudeRunner.is_available()` and `CodexRunner.is_available()` to apply a short timeout,
**so that** a hung `--version` probe cannot stall the entire pipeline indefinitely.

**Acceptance criteria:**
- Both `is_available()` implementations pass `timeout=5` to the subprocess call.
- A `TimeoutExpired` from the probe returns `False` (runner treated as unavailable).
- `test_runners.py` covers the timeout path for both runners.

---

## S2 · Feature-name path sanitization
**As a** user running `pathly go "../../.env"` or any adversarial feature name,
**I want** the engine to reject or normalise unsafe path components before touching the filesystem,
**so that** path-traversal cannot escape the `plans/` directory.

**Acceptance criteria:**
- `DriverConfig` (or `build_parser`) rejects feature names containing `..`, `/`, or `\`.
- A clear error is raised before any filesystem path is constructed.
- `test_team_flow_smoke.py` has a test for an unsafe feature name that asserts the error.

---

## S3 · Documented subprocess failure policy
**As a** developer maintaining the engine,
**I want** a single documented and enforced policy for what happens when a runner exits non-zero,
**so that** the behaviour is predictable and testable rather than implicit.

**Acceptance criteria:**
- `_run_agent` docstring (or inline comment) states the policy: "if `required=True` and exit≠0 → sys.exit(1); if `required=False` and exit≠0 → log warning and emit AgentDoneEvent with the non-zero code."
- `_run_agent` currently logs the non-zero code when `required=False`; if it doesn't, add the log line.
- `test_team_flow_smoke.py` has tests that inject a non-zero runner and verify: `required=True` causes SystemExit, `required=False` continues with the FSM emitting AgentDoneEvent.

---

## S4 · End-to-end integration test (full round-trip)
**As a** maintainer,
**I want** a test that runs `driver.run()` from IDLE to DONE with a mock runner,
**so that** FSM state, EVENTS.jsonl, STATE.json, and PROGRESS.md cannot drift from each other without a test catching it.

**Acceptance criteria:**
- New file `tests/test_e2e.py` contains at least one full-pipeline test (BUILDING → REVIEWING → TESTING → RETRO → DONE) with a mocked runner.
- After the run: STATE.json exists and `current == "DONE"`, EVENTS.jsonl contains AGENT_DONE events for builder + reviewer + tester + quick, PROGRESS.md has no TODO rows.
- Test uses an isolated `tmp_path` with the 4 core plan files pre-written.

---

## S5 · State-stack nesting tests
**As a** developer,
**I want** the FSM reducer's state-stack (BLOCKED_ON_FEEDBACK → BLOCKED_ON_HUMAN stacking) covered by tests,
**so that** deep-nesting edge cases are caught before they surface in production.

**Acceptance criteria:**
- `test_fsm.py` has tests for:
  - BUILDING → FILE_CREATED(REVIEW_FAILURES) → BLOCKED_ON_FEEDBACK → FILE_CREATED(HUMAN_QUESTIONS) → BLOCKED_ON_HUMAN
  - BLOCKED_ON_HUMAN resolved → FILE_DELETED(HUMAN_QUESTIONS) → returns to BLOCKED_ON_FEEDBACK (not BUILDING)
  - BLOCKED_ON_FEEDBACK resolved → FILE_DELETED(REVIEW_FAILURES) → returns to BUILDING
- All three transitions must assert the exact FSM state and `active_feedback_file` at each step.
