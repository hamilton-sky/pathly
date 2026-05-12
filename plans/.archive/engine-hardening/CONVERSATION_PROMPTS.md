# engine-hardening — Conversation Prompts

## Conv 1 — Runner timeouts + path sanitization

```
You are implementing hardening changes for the pathly-engine. This conversation covers two small, independent fixes.

### Fix A — `is_available()` timeout

Files: `pathly-engine/runners/claude.py` and `pathly-engine/runners/codex.py`

Both `is_available()` methods call `run_command([..., "--version"], capture_output=True, check=True)` with NO timeout.
If the CLI hangs, the probe stalls the pipeline forever.

Changes:
1. Add `timeout=5` to the `run_command(...)` call in both `is_available()` implementations.
2. Catch `subprocess.TimeoutExpired` alongside the existing `FileNotFoundError` / `CalledProcessError` and return `False`.
3. In `tests/test_runners.py`, add one test per runner that injects a `run_command` which raises `TimeoutExpired` and asserts `is_available()` returns `False`.

### Fix B — Feature-name path sanitization

File: `pathly-engine/team_flow/config.py`

`DriverConfig.plan_dir` constructs `repo_root / "plans" / self.feature` using raw user input.
A name like `../../.env` would escape the plans/ directory.

Changes:
1. Add a `__post_init__` to `DriverConfig` that raises `ValueError` if `self.feature` contains any of: `..`, `/`, `\`.
   Use a simple check — do NOT use pathlib resolve or os.path for this; just check the string.
   Example: `if any(c in self.feature for c in ('..', '/', '\\')): raise ValueError(f"Unsafe feature name: {self.feature!r}")`
2. In `tests/test_team_flow_smoke.py`, add one test that constructs a `DriverConfig` (or `TeamFlowDriver`) with an unsafe name
   and asserts `ValueError` is raised.

### Do NOT touch
- Anything in orchestrator/
- Any other runner methods (only `is_available()` for Fix A)
- Any plan files

### Verify
Run: `pytest pathly-engine/tests/ -x -q`
All existing tests must still pass. New tests must pass.

Recovery: if verify fails and the fix requires out-of-scope changes, stop and report. If fundamentally broken, run `git checkout` on affected files and retry.

Report: files changed, verify result, stories delivered (S1, S2).
```

---

## Conv 2 — Subprocess failure policy

```
You are documenting and testing the subprocess failure policy in pathly-engine.

### Context
`TeamFlowDriver._run_agent` (pathly-engine/team_flow/manager.py) takes a `required: bool` parameter.
Current behaviour (line ~350):
  - if `return_code != 0` and `required=True`: log + sys.exit(1)
  - if `return_code != 0` and `required=False`: silently continues (no log, no indicator)

The gap: when `required=False` fails, there is no log line and no visible signal. The policy is implicit.

### Changes

1. **Add a docstring** to `_run_agent` that states the policy explicitly:
   ```
   required=True  → non-zero exit causes sys.exit(1); use for stages where failure is unrecoverable
   required=False → non-zero exit logs a warning and continues; FSM still advances via AgentDoneEvent
   ```

2. **Add a log line** for the non-required failure case. After the `if return_code != 0 and required:` block,
   add an `elif return_code != 0:` branch that calls `self.log(f"[WARN] Agent {agent_name} exited {return_code} (non-critical, continuing).")`.
   Keep the existing logic unchanged — just add the log.

3. **Add two tests** in `tests/test_team_flow_smoke.py`:

   Test A — required agent failure causes SystemExit:
   - Create a driver with a mock runner that returns `return_code=1`
   - Call `driver._run_agent(prompt="x", agent_name="builder", required=True)`
   - Assert `SystemExit` is raised

   Test B — non-required agent failure continues:
   - Create a driver with a mock runner that returns `return_code=1`
   - Set driver state to BUILDING with plan files written
   - Call `driver._run_agent(prompt="x", agent_name="reviewer", required=False)`
   - Assert no exception; assert FSM emitted AgentDoneEvent (check EVENTS.jsonl or state.current is not IDLE)

### Do NOT touch
- orchestrator/ files
- runners/ files
- Any plan files

### Verify
Run: `pytest pathly-engine/tests/ -x -q`
All existing tests must still pass. New tests must pass.

Recovery: if verify fails and the fix requires out-of-scope changes, stop and report.

Report: files changed, verify result, story delivered (S3).
```

---

## Conv 3 — End-to-end integration test

```
You are writing a full round-trip integration test for the pathly-engine pipeline driver.

### Context
The existing tests in `test_team_flow_smoke.py` test individual driver methods with mocked runners.
There is no test that calls `driver.run()` end-to-end and verifies that EVENTS.jsonl, STATE.json,
and PROGRESS.md are all consistent after a complete run.

### Task

Create a new file: `pathly-engine/tests/test_e2e.py`

Write one test: `test_full_pipeline_idle_to_done`.

**Setup:**
- Use `tmp_path` (pytest fixture) as the repo root.
- Write the 4 core plan files to `tmp_path/plans/demo/`:
  - `USER_STORIES.md` — minimal content
  - `IMPLEMENTATION_PLAN.md` — minimal content
  - `CONVERSATION_PROMPTS.md` — minimal content
  - `PROGRESS.md` — one conversation row, status TODO:
    ```
    # Progress
    | Conv | Status |
    |------|--------|
    | 1    | TODO   |
    ```
- Write a `git init` so `git diff` calls in the driver don't fail (use subprocess.run).

**Mock runner:**
Create a class `SuccessRunner` that implements the `Runner` protocol:
- `name = "mock"`
- `repo_root` = tmp_path
- `run(prompt)` returns `RunnerResult(return_code=0, usage={"model": "test", "tokens_in": 100, "tokens_out": 50, "cost_usd": 0.01})`
- `is_available()` returns `True`

Pass this runner to `TeamFlowDriver(feature="demo", mode=Mode.FAST, entry="build", repo_root=tmp_path, runner=SuccessRunner(tmp_path))`.

**Patch out the interactive parts:**
The driver may hit pause points or PROGRESS.md checks that need patching. Use monkeypatch to:
- Patch `driver.files.all_conversations_done` to return True (so it exits BUILDING cleanly after one cycle)
- Patch `driver.files.git_is_clean` to return True

**Run:**
Call `driver.run()` — it should complete without raising.

**Assert:**
1. `tmp_path/plans/demo/STATE.json` exists.
2. Parse STATE.json — `state["current"] == "DONE"` (or the FSM may land on RETRO depending on flow — check the actual terminal state and assert it is at least TESTING or later).
3. `tmp_path/plans/demo/EVENTS.jsonl` exists and contains at least one line.
4. Parse EVENTS.jsonl lines — at least one event has `"type": "AGENT_DONE"`.

### Import path
Use: `from pathly import team_flow` and `from pathly.runners.base import RunnerResult`

### Do NOT touch
- Any existing test files
- Any source files
- Any plan files

### Verify
Run: `pytest pathly-engine/tests/test_e2e.py -v`

If the driver hits an interactive prompt that cannot be patched out, stop and report what the blocker is rather than trying to monkey-patch everything. A partial test with a clear TODO comment is acceptable.

Recovery: if verify fails and the fix requires out-of-scope changes, stop and report.

Report: files changed, verify result, story delivered (S4).
```

---

## Conv 4 — State-stack nesting tests

```
You are adding FSM reducer tests for state-stack nesting (deep-blocking) scenarios.

### Context
The pathly-engine FSM reducer (pathly-engine/orchestrator/reducer.py) supports nested blocking:
- BUILDING → FILE_CREATED(REVIEW_FAILURES) → BLOCKED_ON_FEEDBACK
- BLOCKED_ON_FEEDBACK → FILE_CREATED(HUMAN_QUESTIONS) → BLOCKED_ON_HUMAN
- On resolution, the stack unwinds in reverse order

The existing tests in `test_fsm.py` cover basic blocking. Deep nesting (two levels) is not tested.

### Task

Add three tests to `pathly-engine/tests/test_fsm.py`.

Read the existing test_fsm.py first to understand the helper patterns used (how states and events are constructed).

**Test 1 — Two-level block: BUILDING → BLOCKED_ON_FEEDBACK → BLOCKED_ON_HUMAN**

Starting from `State(current=FSMState.BUILDING)`:
1. Emit `FileCreatedEvent(file=FeedbackFile.REVIEW_FAILURES)` → assert `state.current == FSMState.BLOCKED_ON_FEEDBACK`
2. Emit `FileCreatedEvent(file=FeedbackFile.HUMAN_QUESTIONS)` → assert `state.current == FSMState.BLOCKED_ON_HUMAN`
3. Assert `state.active_feedback_file == FeedbackFile.HUMAN_QUESTIONS`

**Test 2 — Unwind one level: BLOCKED_ON_HUMAN → back to BLOCKED_ON_FEEDBACK**

Continuing from Test 1's final state:
1. Emit `FileDeletedEvent(file=FeedbackFile.HUMAN_QUESTIONS)`
2. Assert `state.current == FSMState.BLOCKED_ON_FEEDBACK`
3. Assert `state.active_feedback_file == FeedbackFile.REVIEW_FAILURES`

**Test 3 — Full unwind: BLOCKED_ON_FEEDBACK → back to BUILDING**

Continuing from Test 2's final state:
1. Emit `FileDeletedEvent(file=FeedbackFile.REVIEW_FAILURES)`
2. Assert `state.current == FSMState.BUILDING`
3. Assert `state.active_feedback_file is None`

Each test should be independent (create its own initial state). Use the same event construction patterns as existing tests.

### Do NOT touch
- Any source files (orchestrator/, team_flow/, runners/)
- Any other test files
- Any plan files

### Verify
Run: `pytest pathly-engine/tests/test_fsm.py -v`

Recovery: if the reducer does not support this nesting, stop and report the exact assertion failure rather than modifying the reducer. That is a real finding.

Report: tests added, verify result, story delivered (S5).
```
