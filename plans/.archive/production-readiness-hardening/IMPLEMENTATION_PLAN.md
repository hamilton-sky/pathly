# Production Readiness Hardening — Implementation Plan

## Overview

Close 7 critical gaps found in production-readiness exploration of `pathly-engine`.
All changes are surgical — no architectural rewrites. The FSM stays pure.
3 conversations: reducer+runners (Conv 1), manager (Conv 2), tests (Conv 3).

## Architecture Notes

- **Reducer must stay pure** — no I/O, no side effects. Validation goes in `reduce()` itself,
  returning a new state with `current=BLOCKED_ON_HUMAN` for invalid inputs.
- **Timeout clamp is in the runner** — `ClaudeRunner.run()` and `CodexRunner.run()` are the
  only places that read the timeout env var. Clamp happens there, before `subprocess.run()`.
- **input() replacement is thread-based** — Windows does not support `select.select()` on stdin.
  Use a daemon thread that reads stdin; main thread waits with `thread.join(timeout=N)`.
- **Lockfile path** — `plans/<feature>/.lock` (dot-prefixed, same directory as EVENTS.jsonl).
  Written on `TeamFlowDriver.__init__`, deleted via `atexit.register()` + `try/finally` in `run()`.

## Happy Path (post-fix)

```
env: CLAUDE_AGENT_TIMEOUT=600 (valid)
  → ClaudeRunner reads 600, no clamp, no warning

reducer gets COMMAND event with rigor="lite" (valid)
  → passes through, FSMState set to STORMING

reducer gets AGENT_DONE(agent="builder") while state=PLANNING (invalid pair)
  → soft-escalates: new_state.current = BLOCKED_ON_HUMAN
  → human sees the block, inspects EVENTS.jsonl

driver starts for feature "foo":
  → writes plans/foo/.lock with own PID
  → second "pathly go foo" in another terminal:
      reads .lock, PID alive → error + exit(1)
  → driver exits → .lock deleted
```

---

## Phases

### Phase 1 — Validate COMMAND event metadata   ← Conversation: 1

**File:** `pathly-engine/orchestrator/reducer.py`

**Done when:** A `COMMAND` event with `rigor="garbage"`, `mode="garbage"`, or
`entry_state="garbage"` results in `new_state.current = FSMState.BLOCKED_ON_HUMAN`.
Valid values pass through unchanged.

**Details:**

In the `if event.type == Events.COMMAND:` block (currently lines 62–69), after reading
metadata values, validate each against its enum:

```python
VALID_RIGORS   = {Rigor.LITE, Rigor.STANDARD, Rigor.STRICT}
VALID_MODES    = {Mode.INTERACTIVE, Mode.FAST}
VALID_ENTRIES  = set(vars(FSMState).values())   # all FSMState string values

rigor      = event.metadata.get("rigor", Rigor.STANDARD)
mode       = event.metadata.get("mode", Mode.INTERACTIVE)
entry_state = event.metadata.get("entry_state", FSMState.STORMING)

if rigor not in VALID_RIGORS or mode not in VALID_MODES or entry_state not in VALID_ENTRIES:
    new_state.current = FSMState.BLOCKED_ON_HUMAN
    return new_state
```

Keep the existing assignments above this block (they're fine). Only add the guard.

---

### Phase 2 — Guard `_AGENT_TRANSITIONS` lookup   ← Conversation: 1

**File:** `pathly-engine/orchestrator/reducer.py`

**Done when:** An `AGENT_DONE` event for any `(agent, state)` pair not in `_AGENT_TRANSITIONS`
results in `new_state.current = FSMState.BLOCKED_ON_HUMAN` instead of returning unchanged state.

**Details:**

In the `if event.type == Events.AGENT_DONE:` block (currently lines 71–78), the `if key in _AGENT_TRANSITIONS:` check currently falls through silently. Add an `else`:

```python
if key in _AGENT_TRANSITIONS:
    fast_next, paused_next = _AGENT_TRANSITIONS[key]
    new_state.current = fast_next if state.mode == Mode.FAST else paused_next
else:
    # Invalid (agent, state) pair — escalate rather than silently no-op
    new_state.current = FSMState.BLOCKED_ON_HUMAN
return new_state
```

No other changes to this block.

---

### Phase 3 — Validate and clamp timeout env vars   ← Conversation: 1

**Files:**
- `pathly-engine/runners/claude.py`
- `pathly-engine/runners/codex.py`

**Done when:** Setting `CLAUDE_AGENT_TIMEOUT=0` (or negative, or above 7200) causes a
stderr warning and clamped value. A non-numeric value raises `ValueError`. Valid values
are unchanged. Same behavior for `PATHLY_RUNNER_TIMEOUT` in codex runner.

**Details:**

Extract a helper (add at module level, above the class, in each runner file):

```python
_TIMEOUT_MIN = 60
_TIMEOUT_MAX = 7200

def _validated_timeout(raw: str, env_var: str) -> int:
    try:
        value = int(raw)
    except (ValueError, TypeError):
        raise ValueError(
            f"[pathly] {env_var}={raw!r} is not a valid integer. "
            f"Set it to a number between {_TIMEOUT_MIN} and {_TIMEOUT_MAX}."
        )
    if value < _TIMEOUT_MIN:
        print(
            f"[WARNING] {env_var}={value} is below minimum ({_TIMEOUT_MIN}s). Using {_TIMEOUT_MIN}s.",
            file=sys.stderr,
        )
        return _TIMEOUT_MIN
    if value > _TIMEOUT_MAX:
        print(
            f"[WARNING] {env_var}={value} exceeds maximum ({_TIMEOUT_MAX}s). Using {_TIMEOUT_MAX}s.",
            file=sys.stderr,
        )
        return _TIMEOUT_MAX
    return value
```

In `ClaudeRunner.run()`, replace the current `timeout = int(os.environ.get(...))` block:

```python
raw = os.environ.get(TIMEOUT_ENV_VAR) or os.environ.get(RUNNER_TIMEOUT_ENV_VAR)
if raw is not None:
    timeout = _validated_timeout(raw, TIMEOUT_ENV_VAR if TIMEOUT_ENV_VAR in os.environ else RUNNER_TIMEOUT_ENV_VAR)
else:
    timeout = DEFAULT_TIMEOUT_SECONDS
```

In `CodexRunner.run()`, same pattern using `RUNNER_TIMEOUT_ENV_VAR`.

---

### Phase 4 — Thread-based input() timeout   ← Conversation: 2

**File:** `pathly-engine/team_flow/manager.py`

**Done when:** `ask()` (120s timeout) and `_handle_human_block()` (3600s timeout) exit cleanly
on timeout by emitting `SystemEvent(action="TIMEOUT")` and printing a resume message.

**Details:**

Add a module-level helper:

```python
import threading

_INPUT_TIMEOUT_MSG = (
    "[TIMEOUT] No response after {n}s. Exiting — "
    "state preserved, resume with /pathly go {feature}."
)

def _timed_input(prompt: str, timeout: int) -> str | None:
    """Read a line from stdin with a timeout. Returns None on timeout."""
    result: list[str] = []
    def _read():
        try:
            result.append(input(prompt))
        except EOFError:
            pass
    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout)
    return result[0] if result else None
```

In `ask()` — replace `input().strip().lower()` with:
```python
response = _timed_input(f"  [{' / '.join(options)}]: ", timeout=120)
if response is None:
    print(_INPUT_TIMEOUT_MSG.format(n=120, feature=self.feature))
    self.emit(SystemEvent(action="TIMEOUT", metadata={"location": "ask"}))
    sys.exit(0)
response = response.strip().lower()
```

In `_handle_human_block()` — replace `input()` at line 446 with:
```python
response = _timed_input(
    "\nResolve HUMAN_QUESTIONS.md, then press Enter to continue (or type 'quit'): ",
    timeout=3600,
)
if response is None:
    print(_INPUT_TIMEOUT_MSG.format(n=3600, feature=self.feature))
    self.emit(SystemEvent(action="TIMEOUT", metadata={"location": "_handle_human_block"}))
    sys.exit(0)
response = response.strip().lower()
```

In `_startup_verify()` — replace both `input()` calls (lines 325 and 334) the same way (120s timeout each). These are also short yes/no prompts.

---

### Phase 5 — Check run_claude() return code in feedback loop   ← Conversation: 2

**File:** `pathly-engine/team_flow/manager.py`

**Done when:** A non-zero return code from `run_claude()` inside `_handle_feedback()` emits
`SystemEvent(action="ERROR")` and returns without advancing state. The feedback file remains on disk.

**Details:**

In `_handle_feedback()` (currently lines 399–414), each `self.run_claude(...)` call ignores
the return code. Capture and check it:

```python
if active == FeedbackFile.ARCH_FEEDBACK:
    rc, _ = self.run_claude(self.prompts.fix_arch())
    if rc != 0:
        self._escalate_feedback_error(active, rc)
        return
    self.check_feedback_changes(before, self.get_feedback_files())
    if active not in self.get_feedback_files():
        self.emit(StateTransitionEvent(from_state=self.state.current, to_state=FSMState.BUILDING))
elif active == FeedbackFile.REVIEW_FAILURES:
    self._handle_review_failure(before, active)
elif active == FeedbackFile.DESIGN_QUESTIONS:
    rc, _ = self.run_claude(self.prompts.fix_design())
    if rc != 0:
        self._escalate_feedback_error(active, rc)
        return
    self.check_feedback_changes(before, self.get_feedback_files())
elif active == FeedbackFile.IMPL_QUESTIONS:
    rc, _ = self.run_claude(self.prompts.fix_impl_questions())
    if rc != 0:
        self._escalate_feedback_error(active, rc)
        return
    self.check_feedback_changes(before, self.get_feedback_files())
elif active == FeedbackFile.TEST_FAILURES:
    rc, _ = self.run_claude(self.prompts.fix_tests())
    if rc != 0:
        self._escalate_feedback_error(active, rc)
        return
    self.check_feedback_changes(before, self.get_feedback_files())
```

Add helper method:

```python
def _escalate_feedback_error(self, feedback_file: str, return_code: int) -> None:
    msg = (
        f"[ERROR] Agent failed (exit {return_code}) while resolving {feedback_file}.\n"
        f"Feedback file remains on disk. Human intervention required.\n"
    )
    self.log(msg)
    self.feedback_dir.mkdir(parents=True, exist_ok=True)
    (self.feedback_dir / FeedbackFile.HUMAN_QUESTIONS).write_text(msg, encoding="utf-8")
    self.emit(FileCreatedEvent(file=FeedbackFile.HUMAN_QUESTIONS))
```

---

### Phase 6 — Replace sys.exit(1) on git failure with SystemEvent   ← Conversation: 2

**File:** `pathly-engine/team_flow/manager.py`

**Done when:** A git failure in `_run_building_state()` emits `SystemEvent(action="ERROR")`
with git's stderr in metadata, then exits. No `sys.exit(1)` before event log is updated.

**Details:**

In `_run_building_state()` (lines 248–261), wrap the `subprocess.run()` call:

```python
def _run_building_state(self) -> None:
    self.banner("STAGE 3 - Build (builder)")
    if not self.git_is_clean():
        self.log("Working directory not clean. Commit or stash first.")
        try:
            status = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=str(self.config.repo_root),
                timeout=30,
            )
            self.log(status.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            self.emit(SystemEvent(action="ERROR", metadata={"error": str(exc)}))
            sys.exit(1)
        self.emit(SystemEvent(action="ERROR", metadata={"error": "working tree not clean"}))
        sys.exit(1)
    self._run_agent(self.prompts.build(), Agent.BUILDER, required=True)
```

The key change: `emit(SystemEvent)` is called before any `sys.exit(1)`, so the event log
always records the failure before the process dies.

---

### Phase 7 — PID lockfile   ← Conversation: 2

**File:** `pathly-engine/team_flow/manager.py`

**Done when:** A second `TeamFlowDriver` for the same feature cannot start while one is running.
Stale locks (dead PID) are cleared with a warning. Lock is always released on exit.

**Details:**

Add a module-level helper and integrate into `TeamFlowDriver.__init__`:

```python
import atexit
import os
from pathlib import Path

def _lock_path(plan_dir: Path) -> Path:
    return plan_dir / ".lock"

def _acquire_lock(plan_dir: Path, feature: str) -> None:
    lock = _lock_path(plan_dir)
    if lock.exists():
        try:
            pid = int(lock.read_text().strip())
            try:
                os.kill(pid, 0)   # signal 0: check if process exists
                # Process alive → conflict
                print(
                    f"[ERROR] {feature} is already running (PID {pid}). "
                    f"Stop it before starting a new one."
                )
                sys.exit(1)
            except (ProcessLookupError, PermissionError):
                # PID not found (dead process) — stale lock
                print(f"[WARNING] Removing stale lockfile for {feature} (PID {pid} no longer running).")
                lock.unlink(missing_ok=True)
        except (ValueError, OSError):
            lock.unlink(missing_ok=True)

    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(str(os.getpid()))

def _release_lock(plan_dir: Path) -> None:
    _lock_path(plan_dir).unlink(missing_ok=True)
```

In `TeamFlowDriver.__init__`, after `self.plan_dir` is set:

```python
_acquire_lock(self.plan_dir, self.feature)
atexit.register(_release_lock, self.plan_dir)
```

The `atexit` handler ensures the lock is released even on `sys.exit()` or uncaught exception.

---

## Prerequisites

- `pathly-engine` installs cleanly: `pip install -e pathly-engine/`
- Tests pass before starting: `pytest pathly-engine/tests/ -q`

## Key Decisions

- Reducer stays pure — validation returns `BLOCKED_ON_HUMAN` state, no I/O in reducer
- Thread-based stdin timeout — `select.select()` not used (not portable on Windows stdin)
- Lockfile over flock — simpler, cross-platform, readable by humans debugging stuck state
- Timeout clamp range 60–7200 — 60s minimum prevents accidental instant-kill; 7200s (2h) is a reasonable upper bound for any LLM task
- `atexit` for lock cleanup — handles `sys.exit()` calls scattered across manager; no need to audit every exit point
