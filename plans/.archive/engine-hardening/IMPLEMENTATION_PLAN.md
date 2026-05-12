# engine-hardening — Implementation Plan

## Conversation Breakdown

| Conv | Stories | Scope |
|------|---------|-------|
| 1 | S1, S2 | Runner timeouts + path sanitization |
| 2 | S3 | Subprocess failure policy: document + test |
| 3 | S4 | End-to-end integration test |
| 4 | S5 | State-stack nesting tests |

---

## Conv 1 — Runner timeouts + path sanitization

**Files to touch:**
- `pathly-engine/runners/claude.py` — `is_available()`: add `timeout=5`; handle `TimeoutExpired` → return `False`
- `pathly-engine/runners/codex.py` — same
- `pathly-engine/team_flow/config.py` — `DriverConfig.__post_init__` (or `build_parser` in `manager.py`) — validate `feature` name rejects `..`, `/`, `\`
- `pathly-engine/tests/test_runners.py` — timeout path for both runners
- `pathly-engine/tests/test_team_flow_smoke.py` — unsafe feature name assertion

**Verify:** `pytest pathly-engine/tests/ -x -q`

---

## Conv 2 — Subprocess failure policy

**Files to touch:**
- `pathly-engine/team_flow/manager.py` — `_run_agent`: add docstring/comment stating policy; add `self.log` call for non-zero code when `required=False`
- `pathly-engine/tests/test_team_flow_smoke.py` — two tests: required=True raises SystemExit, required=False continues

**Verify:** `pytest pathly-engine/tests/ -x -q`

---

## Conv 3 — End-to-end integration test

**Files to touch:**
- `pathly-engine/tests/test_e2e.py` — new file; full pipeline from IDLE → DONE with mocked runner

**Verify:** `pytest pathly-engine/tests/test_e2e.py -v`

---

## Conv 4 — State-stack nesting tests

**Files to touch:**
- `pathly-engine/tests/test_fsm.py` — add three nested-blocking scenarios

**Verify:** `pytest pathly-engine/tests/test_fsm.py -v`

---

## Dependency order

1 must precede 2 (both touch `manager.py` / runners).
3 and 4 are independent of each other and can be done in any order after 1 + 2.
