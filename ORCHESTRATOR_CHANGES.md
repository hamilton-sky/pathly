# Orchestrator FSM — Changes Summary

## Problem: Vocabulary Mismatch

The Phase 1 implementation in `orchestrator/` diverged from the canonical spec in `docs/ORCHESTRATOR_FSM.md`. The code used different state names (`BLOCKED`, `IMPLEMENTING`), different event types (`FEEDBACK_EVENT`, `CommandEvent` with `name`/`feature` fields), and tested the code against itself rather than the spec. Tests passed but proved nothing about spec compliance.

This batch of changes realigns all code to the spec vocabulary.

---

## What Changed

### `orchestrator/state.py`

- Replaced the inline comment listing old states (`IDLE`, `STORMING`, `IMPLEMENTING`, `BLOCKED`) with the full 14-state vocabulary from the spec.
- Added five new fields to the `State` dataclass:
  - `rigor: str = "standard"` — workflow strictness level
  - `mode: str = "interactive"` — human pause behavior
  - `retry_count_by_key: dict` — per-key retry counter (key format: `conv-N:FEEDBACK_FILE`)
  - `last_actor: Optional[str]` — which agent last acted
  - `previous_state: Optional[str]` — state before last BLOCKED transition (used to restore on FILE_DELETED)
- Updated `to_dict()` to include all new fields.

### `orchestrator/events.py`

Removed `FeedbackEvent` and the old `CommandEvent` (which had `name`/`feature` fields). Replaced with the full spec event set:

| Class | `type` string | Key fields |
|---|---|---|
| `CommandEvent` | `COMMAND` | `value: str` |
| `AgentDoneEvent` | `AGENT_DONE` | `agent: str` |
| `FileCreatedEvent` | `FILE_CREATED` | `file: str` |
| `FileDeletedEvent` | `FILE_DELETED` | `file: str` |
| `HumanResponseEvent` | `HUMAN_RESPONSE` | `value: str` |
| `NoDiffDetectedEvent` | `NO_DIFF_DETECTED` | — |
| `ImplementCompleteEvent` | `IMPLEMENT_COMPLETE` | — |
| `StateTransitionEvent` | `STATE_TRANSITION` | `from_state`, `to_state` |
| `SystemEvent` | `SYSTEM_EVENT` | `action`, `reason` |

`event_factory()` updated to deserialize all 9 types. Base `Event` class and `to_jsonl()`/`from_jsonl()` unchanged.

### `orchestrator/reducer.py`

Rewrote `reduce()` to handle all 9 event types with spec-correct transitions:

- `COMMAND` → IDLE becomes STORMING; sets `active_feature`, `rigor`, `mode` from metadata
- `AGENT_DONE(architect)` in STORMING → STORM_PAUSED (interactive) or PLANNING (fast)
- `AGENT_DONE(planner)` in PLANNING → PLAN_PAUSED (interactive) or BUILDING (fast)
- `AGENT_DONE(builder)` in BUILDING → REVIEWING
- `AGENT_DONE(reviewer)` in REVIEWING → IMPLEMENT_PAUSED (interactive) or BUILDING (fast)
- `AGENT_DONE(tester)` in TESTING → TEST_PAUSED (interactive) or RETRO (fast)
- `AGENT_DONE(quick)` in RETRO → DONE
- `FILE_CREATED(HUMAN_QUESTIONS.md)` → BLOCKED_ON_HUMAN; saves `previous_state`
- `FILE_CREATED(other)` → BLOCKED_ON_FEEDBACK; saves `previous_state`
- `FILE_DELETED` → restores `previous_state`
- `NO_DIFF_DETECTED` → BLOCKED_ON_HUMAN
- `IMPLEMENT_COMPLETE` → TESTING
- `STATE_TRANSITION` → explicit move to `to_state`
- `SYSTEM_EVENT(RETRY)` → increments `retry_count_by_key[retry_key]`
- `SYSTEM_EVENT(ERROR|TIMEOUT)` → BLOCKED_ON_HUMAN

`reconstruct()` unchanged in signature and behavior — replays events from a list.

### `orchestrator/eventlog.py`

- Changed constructor to support both old `filepath=` style (for tests) and new `feature=` style (for production):
  ```python
  def __init__(self, filepath=None, feature=None, base_path="plans")
  ```
  When `feature` is given, filepath resolves to `plans/<feature>/EVENTS.jsonl`.
- Added `write_state_json(state: State)` — writes `STATE.json` alongside `EVENTS.jsonl` in the same directory.

### `orchestrator/__init__.py`

Updated imports to export all 9 event classes (removed `FeedbackEvent`, added the 7 new classes).

### `orchestrator/test_fsm.py`

Updated all 9 tests to use new event classes and state names:

- `CommandEvent(name=..., feature=...)` → `CommandEvent(value=..., metadata={...})`
- `FeedbackEvent(status="OPEN", ...)` → `FileCreatedEvent(file=..., metadata={...})`
- `FeedbackEvent(status="RESOLVED", ...)` → `FileDeletedEvent(file=..., metadata={...})`
- `SystemEvent(action="ERROR")` now asserts `BLOCKED_ON_HUMAN` (was `BLOCKED`)
- `StateTransitionEvent` target changed from `IMPLEMENTING` to `BUILDING`
- `EventLog` instantiation uses `filepath=` for temp-file paths
- `test_reconstruct_idempotent` asserts `BLOCKED_ON_FEEDBACK` (was `BLOCKED`)
- `test_eventlog_reconstruct_full_cycle` compares dicts excluding `created_at`/`updated_at` (timestamps differ between replays by design)

---

## State Vocabulary (14 states)

```
IDLE
STORMING
STORM_PAUSED
PLANNING
PLAN_PAUSED
BUILDING
REVIEWING
IMPLEMENT_PAUSED
TESTING
TEST_PAUSED
RETRO
BLOCKED_ON_FEEDBACK
BLOCKED_ON_HUMAN
DONE
```

---

## Event Types (9 types)

```
COMMAND            value: str
AGENT_DONE         agent: str
FILE_CREATED       file: str
FILE_DELETED       file: str
HUMAN_RESPONSE     value: str
NO_DIFF_DETECTED   (no payload)
IMPLEMENT_COMPLETE (no payload)
STATE_TRANSITION   from_state: str, to_state: str
SYSTEM_EVENT       action: str, reason: str
```

---

## What Is Still Left to Do

### Phase 2 — Enforce via Orchestrator Skill (est. 1–2 hours)

Wire the FSM into the `team-flow` skill so it is actually consulted before each agent spawn.

- On startup: read `STATE.json` and `EVENTS.jsonl` for the target feature (if they exist).
- Before spawning any agent: call `reduce(state, event)` and check the result.
- Add guard: if any file in `plans/<feature>/feedback/` exists, emit `FILE_CREATED` and block.
- Add guard: if `retry_count_by_key[key] > 2`, escalate — write `HUMAN_QUESTIONS.md` and move to `BLOCKED_ON_HUMAN`.
- Add guard: if builder finished but `git diff --cached` is empty, emit `NO_DIFF_DETECTED`.
- After each transition: write `STATE.json` via `EventLog.write_state_json()` and append the event to `EVENTS.jsonl`.

No agent prompts or plan file formats need to change.

### Phase 3 — State Recovery (est. 1 hour)

Implement `orchestrator --recover <feature>` (or a `/team-flow <feature> --recover` path) that reconstructs state from disk when `STATE.json` is stale or missing.

Recovery precedence (from `docs/ORCHESTRATOR_FSM.md`):

1. If `HUMAN_QUESTIONS.md` exists → `BLOCKED_ON_HUMAN`
2. If any feedback file exists → `BLOCKED_ON_FEEDBACK`
3. If all conversations done and tests not passed → `TESTING` or `TEST_PAUSED`
4. If any conversation is TODO → `BUILDING` or `IMPLEMENT_PAUSED`
5. If plan files exist but no build started → `PLAN_PAUSED`
6. If only storm output exists → `STORM_PAUSED`
7. Otherwise → `IDLE`

After recovery, update `STATE.json` and append a recovery event to `EVENTS.jsonl`.

### Phase 4 — Audit Logs and Observability (est. 30 minutes)

Each transition should write a structured EVENTS.jsonl entry that includes `fromState`, `toState`, `action`, and `timestamp` (not just the event payload). This enables the `/verify-state` skill to report:

```
Conversation 1: 2 feedback cycles. Total time: 35 mins.
No current blocks. Ready to advance to conversation 2.
```

Also: add a `--replay` flag that prints the full state history from EVENTS.jsonl without re-running agents.

---

## How to Test

```bash
cd c:\Users\Yafit\claude-agents-framework
python -m pytest orchestrator/test_fsm.py -v
```

Expected output: 9 passed, 0 failed.

To run as a script (without pytest):

```bash
python orchestrator/test_fsm.py
```
