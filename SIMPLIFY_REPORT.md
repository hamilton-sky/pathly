# Code Review — Simplify Report

**Date:** 2026-05-03  
**Scope:** Commits `3ff85ef`–`e9e87df` — orchestrator FSM implementation  
**Files reviewed:** `orchestrator/events.py`, `orchestrator/reducer.py`, `orchestrator/state.py`, `orchestrator/eventlog.py`, `orchestrator/test_fsm.py`

---

## 1. Code Reuse

### 1.1 Repeated dict-filtering in `event_factory`
**Location:** [orchestrator/events.py:108-127](orchestrator/events.py#L108-L127)

Every branch does the same inline dict comprehension with a different allowed-key set:
```python
return CommandEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata", "value")})
return AgentDoneEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata", "agent")})
# … 7 more identical patterns
```

**Recommended fix:** Extract a module-private helper and a registry dict:
```python
_BASE_KEYS = ("type", "timestamp", "metadata")

_EVENT_REGISTRY: dict[str, tuple[type, tuple[str, ...]]] = {
    "COMMAND":            (CommandEvent,          (*_BASE_KEYS, "value")),
    "AGENT_DONE":         (AgentDoneEvent,         (*_BASE_KEYS, "agent")),
    "FILE_CREATED":       (FileCreatedEvent,        (*_BASE_KEYS, "file")),
    "FILE_DELETED":       (FileDeletedEvent,        (*_BASE_KEYS, "file")),
    "HUMAN_RESPONSE":     (HumanResponseEvent,      (*_BASE_KEYS, "value")),
    "NO_DIFF_DETECTED":   (NoDiffDetectedEvent,     _BASE_KEYS),
    "IMPLEMENT_COMPLETE": (ImplementCompleteEvent,  _BASE_KEYS),
    "STATE_TRANSITION":   (StateTransitionEvent,    (*_BASE_KEYS, "from_state", "to_state")),
    "SYSTEM_EVENT":       (SystemEvent,             (*_BASE_KEYS, "action", "reason")),
}

def event_factory(event_dict: dict) -> Event:
    cls, keys = _EVENT_REGISTRY.get(event_dict.get("type"), (Event, _BASE_KEYS))
    return cls(**{k: v for k, v in event_dict.items() if k in keys})
```

---

### 1.2 Dual-source field access pattern repeated 5+ times in `reducer.py`
**Location:** [orchestrator/reducer.py:40](orchestrator/reducer.py#L40), [L48](orchestrator/reducer.py#L48), [L85](orchestrator/reducer.py#L85), [L115](orchestrator/reducer.py#L115), [L122](orchestrator/reducer.py#L122)

The pattern `event.metadata.get("X", getattr(event, "X", ""))` appears everywhere to accommodate both metadata-dict and direct-attribute callers.

**Recommended fix:** Extract a single helper:
```python
def _field(event: Event, name: str, default: str = "") -> str:
    return event.metadata.get(name, getattr(event, name, default))
```
Then call `_field(event, "agent")` instead of the inline expression.

---

### 1.3 Tempfile setup/teardown duplicated across two tests
**Location:** [orchestrator/test_fsm.py:152-179](orchestrator/test_fsm.py#L152-L179) and [L184-222](orchestrator/test_fsm.py#L184-L222)

Both `test_eventlog_persist_and_read` and `test_eventlog_reconstruct_full_cycle` repeat the exact same tempfile pattern.

**Recommended fix:** Use a pytest fixture in `conftest.py`:
```python
@pytest.fixture
def tmp_jsonl(tmp_path):
    return str(tmp_path / "events.jsonl")
```
`tmp_path` is a built-in pytest fixture that handles cleanup automatically — no `try/finally` needed.

---

### 1.4 Timestamp generation scattered across three files
**Location:** [orchestrator/events.py:14](orchestrator/events.py#L14), [orchestrator/state.py:35-36](orchestrator/state.py#L35-L36), [orchestrator/reducer.py:32](orchestrator/reducer.py#L32)

`datetime.now(datetime.UTC).isoformat()` appears three times.

**Recommended fix:** One helper in a shared `utils.py`:
```python
def utc_now() -> str:
    return datetime.now(datetime.UTC).isoformat()
```

---

## 2. Code Quality

### 2.1 Stringly-typed state, agent, mode, and file names (critical)
**Locations:**
- State names like `"STORMING"`, `"BUILDING"`, `"BLOCKED_ON_FEEDBACK"` — [reducer.py:39-140](orchestrator/reducer.py#L39-L140), [test_fsm.py](orchestrator/test_fsm.py) (~30 occurrences total)
- Agent names `"architect"`, `"builder"`, `"reviewer"` etc. — [reducer.py:51-79](orchestrator/reducer.py#L51-L79)
- Mode values `"fast"`, `"interactive"` — [reducer.py:52-73](orchestrator/reducer.py#L52-L73), [state.py:24-25](orchestrator/state.py#L24-L25)
- File names `"REVIEW_FAILURES.md"`, `"HUMAN_QUESTIONS.md"` — [reducer.py:88](orchestrator/reducer.py#L88), [test_fsm.py:67](orchestrator/test_fsm.py#L67)

A typo anywhere silently produces wrong behavior with no error.

**Recommended fix:** Define these as `Literal` types or module constants:
```python
# states.py (or top of state.py)
class FSMState:
    IDLE = "IDLE"
    STORMING = "STORMING"
    BUILDING = "BUILDING"
    BLOCKED_ON_FEEDBACK = "BLOCKED_ON_FEEDBACK"
    BLOCKED_ON_HUMAN = "BLOCKED_ON_HUMAN"
    # …

class Agent:
    ARCHITECT = "architect"
    BUILDER = "builder"
    # …

class FeedbackFile:
    REVIEW_FAILURES = "REVIEW_FAILURES.md"
    HUMAN_QUESTIONS = "HUMAN_QUESTIONS.md"
    # …
```

---

### 2.2 Nested conditionals — repeated `state.mode == "fast"` inside AGENT_DONE handler
**Location:** [orchestrator/reducer.py:51-79](orchestrator/reducer.py#L51-L79)

The same two-branch pattern `if state.mode == "fast": <auto> else: <pause>` repeats for every agent. The branching logic is the same; only the state names differ.

**Recommended fix:** Use a transition table:
```python
_AGENT_TRANSITIONS = {
    # (agent, from_state): (fast_state, paused_state)
    ("architect", "STORMING"):  ("PLANNING",  "STORM_PAUSED"),
    ("planner",   "PLANNING"):  ("BUILDING",  "PLAN_PAUSED"),
    ("builder",   "BUILDING"):  ("REVIEWING", "REVIEWING"),
    ("reviewer",  "REVIEWING"): ("BUILDING",  "IMPLEMENT_PAUSED"),
    ("tester",    "TESTING"):   ("RETRO",     "TEST_PAUSED"),
    ("quick",     "RETRO"):     ("DONE",      "DONE"),
}

if event.type == "AGENT_DONE":
    agent = _field(event, "agent")
    new_state.last_actor = agent
    key = (agent, state.current)
    if key in _AGENT_TRANSITIONS:
        fast_next, paused_next = _AGENT_TRANSITIONS[key]
        new_state.current = fast_next if state.mode == "fast" else paused_next
    return new_state
```

---

### 2.3 Latent bug — `previous_state` is a single field, not a stack
**Location:** [orchestrator/state.py:32](orchestrator/state.py#L32), [orchestrator/reducer.py:86-100](orchestrator/reducer.py#L86-L100)

If two feedback files appear in sequence before the first is resolved, `FILE_CREATED` for the second overwrites `previous_state`. When both are deleted, the state restores to the second file's predecessor only — the original pre-block state is lost.

**Recommended fix:** Use a list as a stack:
```python
state_stack: list[str] = field(default_factory=list)

# On FILE_CREATED:
new_state.state_stack = [*state.state_stack, state.current]

# On FILE_DELETED:
if state.state_stack:
    new_state.current = state.state_stack[-1]
    new_state.state_stack = state.state_stack[:-1]
```

---

### 2.4 State dataclass claims "immutable" but contains a mutable dict
**Location:** [orchestrator/state.py:10](orchestrator/state.py#L10) (docstring), [state.py:28](orchestrator/state.py#L28) (field)

`retry_count_by_key: dict = field(default_factory=dict)` is a plain mutable dict. `reducer.py:28` copies it shallowly with `dict(...)`, but nothing prevents an external caller from mutating `state.retry_count_by_key` directly, which breaks the event-sourced invariant.

**Recommended fix:** Either use `@dataclass(frozen=True)` with `types.MappingProxyType`, or update the docstring to "treat as immutable — never mutate after creation" and remove the "Immutable" claim.

---

### 2.5 `event_factory` grows unboundedly with every new event type
**Location:** [orchestrator/events.py:104-128](orchestrator/events.py#L104-L128)

Every new event type requires a new `elif` branch. Combined with fix 1.1 (registry), this is eliminated automatically.

---

### 2.6 Redundant `type` field redeclaration on every subclass
**Location:** [orchestrator/events.py:36,44,52,60,68,76,83,90,99](orchestrator/events.py#L36)

Every dataclass subclass redeclares `type: str = "EVENT_TYPE"`. This is necessary for dataclass field ordering but becomes noise if the base `type` field were handled via `__post_init__` or a classvar. Low priority — document the reason (dataclass default ordering) with a single comment on the base class rather than leaving it implicit.

---

### 2.7 Tests use `print("✅ …")` instead of pytest assertions
**Location:** [orchestrator/test_fsm.py:38,55,74,89,105,120,147,175,218](orchestrator/test_fsm.py#L38)

Print statements are swallowed by pytest's output capture. The test output won't appear in CI logs on success, and the custom `run_all_tests()` runner duplicates what `pytest` already does.

**Recommended fix:** Remove all `print("✅ …")` lines. Remove `run_all_tests()` and the `if __name__ == "__main__"` block. Run tests with `pytest orchestrator/test_fsm.py`.

---

### 2.8 Unnecessary comments explaining WHAT
**Location:**
- [orchestrator/events.py:45](orchestrator/events.py#L45) — `# e.g. "architect", "planner", ...` (just lists possible values)
- [orchestrator/state.py:27](orchestrator/state.py#L27) — `# key is "conv-N:FEEDBACK_FILE", value is retry count` (the type annotation says this)
- [orchestrator/reducer.py](orchestrator/reducer.py) — section heading comments `# === COMMAND ===` add no information the `if event.type ==` already provides

**Recommended fix:** Delete these; keep only the `previous_state` comment which explains a non-obvious design constraint.

---

## 3. Efficiency

### 3.1 TOCTOU — existence check before file open/remove
**Location:** [orchestrator/eventlog.py:38-39](orchestrator/eventlog.py#L38-L39) (`read_all`), [eventlog.py:63-64](orchestrator/eventlog.py#L63-L64) (`clear`)

```python
# current — TOCTOU
if not os.path.exists(self.filepath):
    return []
with open(self.filepath, "r") as f: ...

# fix
try:
    with open(self.filepath, "r") as f: ...
except FileNotFoundError:
    return []
```

Same pattern in `clear()`:
```python
# fix
try:
    os.remove(self.filepath)
except FileNotFoundError:
    pass
```

---

### 3.2 `reconstruct_state()` replays entire log on every call — no checkpoint
**Location:** [orchestrator/eventlog.py:50-53](orchestrator/eventlog.py#L50-L53)

Every call to `reconstruct_state()` reads all lines from disk and replays all events through `reduce()`. For typical feature workflows (50–200 events) this is imperceptible, but grows linearly and has no upper bound.

**Recommended fix:** Periodically write a snapshot via the existing `write_state_json()`, then use it as a starting point:
```python
def reconstruct_state(self) -> State:
    snapshot = self._load_snapshot()  # reads STATE.json if present
    if snapshot:
        # replay only events after snapshot.event_count
        all_events = self.read_all()
        tail = all_events[snapshot.event_count:]
        return reconstruct_tail(tail, starting_state=snapshot)
    return reconstruct(self.read_all())
```

---

### 3.3 `retry_count_by_key` dict copied on every event, even non-RETRY ones
**Location:** [orchestrator/reducer.py:28](orchestrator/reducer.py#L28)

`dict(state.retry_count_by_key)` runs on every call to `reduce()`. At current scale (dict typically has 1–5 keys) this costs nothing, but the copy is unnecessary for the ~95% of events that don't touch retry state.

**Recommended fix:** Copy lazily inside the `RETRY` branch only:
```python
if action == "RETRY" and retry_key:
    new_retry = dict(state.retry_count_by_key)
    new_retry[retry_key] = new_retry.get(retry_key, 0) + 1
    new_state.retry_count_by_key = new_retry
```
And in the `State` copy at the top, share the reference: `retry_count_by_key=state.retry_count_by_key` (safe because we only ever replace, never mutate).

---

## Priority Summary

| # | Issue | Severity | Status | Location |
|---|-------|----------|--------|----------|
| 2.3 | `previous_state` is single field — data loss on nested blocks | **High** | ✅ Fixed (2026-05-04) | state.py, reducer.py |
| 3.1 | TOCTOU existence checks | Medium | ✅ Fixed (2026-05-04) | eventlog.py |
| 2.7 | Print-based test output, custom runner | Medium | ✅ Fixed (2026-05-04) | test_fsm.py |
| — | `datetime.UTC` on class instead of module (bonus bug) | **High** | ✅ Fixed (2026-05-04) | events.py, state.py, reducer.py |
| 2.1 | Stringly-typed state/agent/file names | **High** | Open | reducer.py, test_fsm.py |
| 2.2 | Nested conditionals in AGENT_DONE handler | Medium | Open | reducer.py:51-79 |
| 1.1 | `event_factory` dict-filtering duplication | Medium | Open | events.py:108-127 |
| 1.2 | Dual-source field access repeated 5× | Medium | Open | reducer.py (multiple) |
| 2.4 | Mutable dict in "immutable" State | Medium | Open | state.py:28 |
| 1.3 | Tempfile teardown duplicated in tests | Low | Open | test_fsm.py:152-222 |
| 1.4 | `utc_now()` timestamp scattered | Low | Open | events.py, state.py, reducer.py |
| 3.2 | No snapshot/checkpoint for event replay | Low | Open | eventlog.py:50-53 |
| 3.3 | Unnecessary dict copy on every event | Low | Open | reducer.py:28 |
| 2.8 | Unnecessary WHAT-comments | Low | Open | events.py, state.py, reducer.py |
| 2.6 | Redundant `type` re-declaration on subclasses | Cosmetic | Open | events.py |
