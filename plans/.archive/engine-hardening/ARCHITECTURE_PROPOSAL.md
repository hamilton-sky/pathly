# engine-hardening — Architecture Proposal

## Layer map

```
runners/        ← Conv 1: is_available() timeout changes
team_flow/      ← Conv 1 (config.py sanitization), Conv 2 (manager.py policy)
tests/          ← Conv 1, 2, 3, 4: new/extended test files
orchestrator/   ← NOT touched (FSM reducer is read-only for Conv 4 — tests only)
```

## Design decisions

### D1 — Path sanitization in `DriverConfig.__post_init__`, not in `build_parser`

`DriverConfig` is used by both the CLI (`build_parser`) and the test harness (direct construction).
Putting the guard in `__post_init__` ensures protection is enforced regardless of entry point.
`build_parser` does not need a duplicate guard — it constructs `TeamFlowDriver` which constructs `DriverConfig`.

Rejected: sanitizing in `build_parser` only — leaves direct Python API callers unprotected.

### D2 — Simple string check, not `Path.resolve()`

`Path.resolve()` would canonicalize symlinks and relative segments, but requires the path to exist
and behaves differently on Windows vs Unix. A string check (`".." in name`) is portable, fast,
and makes the intent obvious. The check runs before any filesystem access.

### D3 — `is_available()` timeout = 5 seconds

`--version` on any CLI should return in under 1 second. 5 seconds gives headroom for slow
startup (e.g., nvm, pyenv) without contributing meaningfully to the pipeline duration.
Default runner timeout is 1800s — this is a separate, much shorter probe-only timeout.

### D4 — Conv 4 is test-only (no reducer changes) — **Superseded by D6**

The nesting tests in Conv 4 are verification, not fixes. If the reducer fails the nesting tests,
that surfaces a real gap to fix in a follow-on feature. Do not preemptively change the reducer.

### D5 — E2E test uses Mode.FAST

`Mode.FAST` skips all `input()` calls in the driver. This is the only way to run `driver.run()`
without monkey-patching `input`. The test uses `Mode.FAST` explicitly; this is the correct
approach for headless testing of the driver.

### D6 — `feedback_stack` parallels `state_stack` for nested-block restoration

`State` gains a new field `feedback_stack: list = field(default_factory=list)` that mirrors
`state_stack`. On every `FILE_CREATED` push, the *current* `active_feedback_file` is pushed
onto `feedback_stack` BEFORE being overwritten with the new file. On every `FILE_DELETED`
pop, the value is popped and restored to `active_feedback_file`.

```
state_stack:    [BUILDING]              [BUILDING, BLOCKED_ON_FEEDBACK]
feedback_stack: [None]                  [None, REVIEW_FAILURES.md]
                ^ after REVIEW push     ^ after HUMAN_QUESTIONS push
```

Invariant: `len(feedback_stack) == len(state_stack)` at all times.

Backward-compatible: existing STATE.json files without `feedback_stack` load with empty
list (default_factory). The unwind path falls back to clearing `active_feedback_file` to
None when `feedback_stack` is empty, matching prior behavior.

Rejected alternatives:
- Storing `(state, feedback_file)` tuples on `state_stack` — breaks JSON shape and any
  external reader that expects a list of strings.
- Encoding the prior file in the FILE_DELETED event metadata — pushes responsibility to
  the event producer; the reducer should be the single source of truth for stack discipline.
