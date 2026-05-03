# FSM Implementation Plan: Making the Orchestrator Mechanical

## Current Status

| Phase | Status | Notes |
|---|---|---|
| Phase 1 — Core FSM Logic | **DONE** | `orchestrator/` module ships: state.py, events.py, reducer.py, eventlog.py. 9/9 tests passing. |
| Phase 2 — Enforce via Orchestrator Skill | TODO | Wire FSM into `team-flow` skill |
| Phase 3 — State Recovery | TODO | `--recover` flag + disk-first reconstruction |
| Phase 4 — Audit Logs & Observability | TODO | `/verify-state` FSM reporting |

See `ORCHESTRATOR_CHANGES.md` for a full description of what Phase 1 delivered.

---

## Executive Summary

Your instinct is right. A thin FSM layer is the next keystone change. This adds mechanical enforcement of the rules ("don't advance with open feedback", "max 2 retries per conversation") without overbuilding into a full daemon/scheduler. The system remains file-driven, but with explicit state tracking and event logs.

**Payoff:** Recovery, deterministic blocking, retry accounting, audit trails, and reproducibility.
**Risk:** None if phased correctly — the FSM is optional infrastructure under the existing agents.

---

## Current State vs. Desired State

### Today
- Rules exist only in agent instructions ("builder, don't submit until reviewer passes")
- State is implicit in chat memory and PROGRESS.md
- Recovery means reading chat history and re-inferring where we are
- Retry logic is advisory ("try max 2 times")
- Feedback loops are implicit ("check for REVIEW_FAILURES.md after implementing")

### Tomorrow
- Rules are enforced by the FSM (`if feedback.anyOpen: block`)
- State is explicit in `STATE.json` and `EVENTS.jsonl`
- Recovery means reading disk and reconstructing state from files + logs
- Retry counts are tracked per conversation + feedback file, enforced before spawning
- Feedback loops are deterministic transitions in the state machine

---

## Why This Matters

The current system works *when agents follow instructions*. But:

1. **Agent drift**: A well-meaning builder might skip review if they "feel confident."
2. **Lost state**: If chat resets, you can't recover the current pipeline position without manual inspection.
3. **Retry mystery**: When `REVIEW_FAILURES.md` keeps appearing, there's no audit trail of how many times or why.
4. **Manual recovery**: Resuming after a network error requires re-reading PROGRESS.md and inferring what happened.

An FSM eliminates guesswork. It makes the rules mechanical.

---

## Phased Implementation

### Phase 1: Core FSM Logic (2-3 hours)

**Goal:** Implement the state machine transition logic without changing agent behavior or the pipeline.

**Deliverables:**
1. `STATE.json` schema + `EVENTS.jsonl` format (JSON)
2. A `reducer.py` (or `.md` pseudocode) that implements `state + event → new_state + action`
3. Populated `EVENTS.jsonl` by the orchestrator after each agent completes

**Files to create:**
- `~/.claude/orchestrator/state.py` — State and Event types
- `~/.claude/orchestrator/reducer.py` — Pure `reduce(state, event, context) → (new_state, action)`
- `~/.claude/orchestrator/recovery.py` — Reconstruct state from disk on startup

**No agent changes required.** The FSM runs in parallel with the existing agents.

**Concrete example:**
```json
{
  "feature": "hotel-search",
  "state": "BUILDING",
  "mode": "interactive",
  "rigor": "standard",
  "currentConversation": 1,
  "retryCountByKey": {
    "conv-1:REVIEW_FAILURES.md": 1
  },
  "activeFeedbackFile": "REVIEW_FAILURES.md",
  "timestamp": "2026-05-03T14:22:00Z"
}
```

Each event appended to `EVENTS.jsonl`:
```jsonl
{"event": {"type": "COMMAND", "value": "/team-flow hotel-search"}, "fromState": "IDLE", "toState": "STORMING", "action": "spawn(architect)", "timestamp": "2026-05-03T14:20:00Z"}
{"event": {"type": "AGENT_DONE", "agent": "architect"}, "fromState": "STORMING", "toState": "STORM_PAUSED", "action": "pause(human)", "timestamp": "2026-05-03T14:22:00Z"}
```

---

### Phase 2: Enforce via Orchestrator Skill (1-2 hours)

**Goal:** Make the orchestrator a stateful agent that checks rules before spawning builders/reviewers.

**Changes:**
1. Update `team-flow` skill to call the FSM reducer before each decision
2. Teach `team-flow` to read `STATE.json` + `EVENTS.jsonl` on startup
3. Add guard: `if feedback.anyOpen: stop and report which file + whose job`
4. Add guard: `if retryCount[key] > 2: escalate to HUMAN_QUESTIONS.md`
5. Add guard: `if builder finished but git diff is empty: escalate [STALL]`

**Concrete example — what changes in team-flow:**
```markdown
## Before (today):
After builder completes:
  spawn(reviewer)  ← hope the builder followed the rules

## After (with FSM):
After builder completes:
  Event: AGENT_DONE(builder)
  Derive: retryCountByKey["conv-1:REVIEW_FAILURES.md"] = 1
  If feedback.anyOpen:
    read priority order → architect for ARCH_FEEDBACK, builder for REVIEW_FAILURES
  Else:
    new_state = REVIEWING
    spawn(reviewer)
```

**No changes to agents.** The FSM is policy enforcement in the orchestrator.

---

### Phase 3: Add State Recovery (1 hour)

**Goal:** When `/team-flow` is invoked with a feature name, recover the exact state from disk.

**Implementation:**
```python
def recover_state(feature: str) -> State:
  """Read plans/<feature>/ and reconstruct current state."""
  
  # Precedence: explicit state wins, then infer from files
  if exists(STATE.json):
    cached_state = read_json("plans/{feature}/STATE.json")
  
  # Verify against ground truth
  feedback_files = ls("plans/{feature}/feedback/")
  progress = read_md("plans/{feature}/PROGRESS.md")
  
  # Check guards
  if "HUMAN_QUESTIONS.md" in feedback_files:
    return State(current="BLOCKED_ON_HUMAN", ...)
  
  if any(feedback_files):
    return State(current="BLOCKED_ON_FEEDBACK", ...)
  
  # Derive from PROGRESS
  if all_conversations_done(progress):
    if has_test_failures(progress):
      return State(current="TESTING", ...)
    else:
      return State(current="IMPLEMENT_PAUSED", ...)
  
  # Continue normally
  return cached_state or State(current="IDLE")
```

**Concrete workflow:**
1. User runs `/team-flow hotel-search --recover`
2. Orchestrator reads `STATE.json` (if exists) and `EVENTS.jsonl` (if exists)
3. Verifies against `plans/hotel-search/feedback/`, `PROGRESS.md`, git diff
4. If cache is stale: disk wins. Update `STATE.json` and append recovery event.
5. Print: `Recovered to state: BLOCKED_ON_FEEDBACK. Active feedback: REVIEW_FAILURES.md. Builder must fix.`

---

### Phase 4: Audit Logs & Observability (30 mins)

**Goal:** Every state transition produces a log entry that can be audited later.

**EVENTS.jsonl format (one event per line):**
```jsonl
{"event":{"type":"COMMAND","value":"/team-flow hotel-search"},"fromState":"IDLE","toState":"STORMING","action":"spawn(architect)","timestamp":"2026-05-03T14:20:00Z"}
{"event":{"type":"AGENT_DONE","agent":"architect"},"fromState":"STORMING","toState":"STORM_PAUSED","action":"pause(user)","timestamp":"2026-05-03T14:22:00Z"}
{"event":{"type":"FILE_CREATED","file":"REVIEW_FAILURES.md"},"fromState":"IMPLEMENTING","toState":"BLOCKED_ON_FEEDBACK","action":"spawn(builder)","timestamp":"2026-05-03T14:45:00Z"}
{"event":{"type":"FILE_DELETED","file":"REVIEW_FAILURES.md"},"fromState":"BLOCKED_ON_FEEDBACK","toState":"IMPLEMENTING","action":"continue","timestamp":"2026-05-03T14:55:00Z"}
```

**Reporting command:**
```
/verify-state hotel-search
  → reads EVENTS.jsonl
  → prints: "Conversation 1: 2 feedback cycles (REVIEW_FAILURES.md, then DESIGN_QUESTIONS.md). Total time: 35 mins."
  → prints: "No current blocks. Ready to advance to conversation 2."
```

---

## Implementation Approach: No Rewrites

**Key principle:** The FSM is **additive infrastructure**, not a rewrite.

1. **Agents stay exactly as-is.** Builder still reads `CONVERSATION_PROMPTS.md`. Reviewer still checks rules. No agent changes.

2. **Existing files stay exactly as-is.** `PROGRESS.md`, `CONVERSATION_PROMPTS.md`, feedback files — all unchanged.

3. **New files are alongside, not replacing:**
   - `STATE.json` — cache of current state (for fast lookup, not required for recovery)
   - `EVENTS.jsonl` — append-only audit log (required for `strict` rigor, optional for `lite`/`standard`)

4. **FSM is policy, not mechanism.** It says "enforce this rule" but doesn't implement the agent work itself.

---

## Concrete File Structure After Phase 1

```
plans/hotel-search/
├── USER_STORIES.md           ← unchanged
├── IMPLEMENTATION_PLAN.md     ← unchanged
├── PROGRESS.md               ← unchanged (but now orchestrator reads it more carefully)
├── CONVERSATION_PROMPTS.md   ← unchanged
├── HAPPY_FLOW.md             ← unchanged
├── EDGE_CASES.md             ← unchanged
├── ARCHITECTURE_PROPOSAL.md  ← unchanged
├── FLOW_DIAGRAM.md           ← unchanged
├── STATE.json                ← NEW: {state, mode, rigor, ...}
├── EVENTS.jsonl              ← NEW: append-only event log
└── feedback/
    ├── ARCH_FEEDBACK.md      ← unchanged (written by reviewer, deleted by architect)
    ├── REVIEW_FAILURES.md    ← unchanged
    ├── IMPL_QUESTIONS.md     ← unchanged
    ├── DESIGN_QUESTIONS.md   ← unchanged
    ├── TEST_FAILURES.md      ← unchanged
    └── HUMAN_QUESTIONS.md    ← unchanged
```

---

## Rules Enforced by FSM

### Rule 1: No advance with open feedback
```
Guard: if any file in plans/<feature>/feedback/ exists
  action: BLOCKED_ON_FEEDBACK
  effect: do not spawn next agent, show which file and whose job to resolve
```

### Rule 2: Max 2 retries per conversation + feedback file
```
Guard: if retryCountByKey["conv-N:FEEDBACK_FILE"] > 2
  action: escalate to BLOCKED_ON_HUMAN
  effect: write HUMAN_QUESTIONS.md, stop, report to user
  note: each file's retry counter is independent
```

### Rule 3: Zero-diff escalation (auto-detect stall loops)
```
Guard: if builder finishes REVIEW_FAILURES.md but git diff --cached is empty
  action: escalate to BLOCKED_ON_HUMAN
  effect: write HUMAN_QUESTIONS.md [STALL], stop
  note: builder acknowledged violations but didn't fix code
```

### Rule 4: Deterministic feedback priority
```
When BLOCKED_ON_FEEDBACK:
  for each file in priority order [HUMAN_QUESTIONS, ARCH_FEEDBACK, DESIGN_QUESTIONS, IMPL_QUESTIONS, REVIEW_FAILURES, TEST_FAILURES]:
    if file exists: route to responsible agent, stop
  effect: only one agent ever addresses one feedback file at a time
```

### Rule 5: All conversations must complete before test
```
Guard: if state = TESTING and any conversation status != DONE in PROGRESS.md
  action: error
  effect: fail fast, report which conversation is still TODO
```

---

## Why This Approach Avoids Overengineering

1. **No daemon.** The FSM runs during `/team-flow`, not in the background.
2. **No real-time watch.** No inotify or file watchers. Check disk when needed.
3. **No new language.** The FSM is expressed in plain Python or pseudocode.
4. **No new services.** No database, no queue, no RPC. Just files + simple logic.
5. **Backward compatible.** Old plans without `STATE.json` or `EVENTS.jsonl` still work.
6. **Testable.** The reducer is a pure function: `(state, event, context) → (new_state, action)`.

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| FSM logic gets complex | Keep it simple: 1 event → 1 transition. If multiple things need to happen, that's multiple events. |
| State cache diverges from ground truth | Always prefer disk (feedback files, PROGRESS.md). STATE.json is cache only. Reconstruct on every startup. |
| Old plans become invalid | STATE.json and EVENTS.jsonl are optional. Plan files work without them. Safe to backfill. |
| Retry logic is too strict | Retry budget is per (conversation, feedback file) pair, not global. Failed ACs in conv 1 don't consume retries for conv 2. |
| Agents deviate from rules | FSM enforces before agents run, not after. Blocking is mechanical. |

---

## Adoption Timeline

**~~Week 1: Phase 1 (FSM core logic).~~** DONE — `orchestrator/` module ships with 9/9 tests passing. Vocabulary aligned to spec.

**Next:** Phase 2 (enforce in team-flow). Update `team-flow` skill to call `reduce()` + `EventLog.append()` before each decision.

**Then:** Phase 3 (recovery) + Phase 4 (audit logs). Ship recovery and observability.

No agents need updating until **after** Phase 2 ships. The framework is safe to use during implementation.

---

## What Doesn't Change

- Agent behavioral contracts
- Skill step sequencing
- Feedback file formats
- Plan file templates
- User commands (`/go`, `/team-flow`, `/help`, etc.)
- Builder prompts or reviewing logic
- Rigor modes (lite/standard/strict) — FSM respects them

---

## What Gets Better

1. **Determinism:** State transitions are explicit, not inferred.
2. **Recovery:** Unplug at any point, plug back in, and the system knows where it was.
3. **Auditability:** Full event log for compliance/debugging.
4. **Enforcement:** Rules are checked before rules are needed, not hoped for during execution.
5. **Clarity:** Read `STATE.json` or `EVENTS.jsonl` and immediately know what happened and why.

---

## Verdict: Go for It

**Strongly recommended as the next keystone change.**

The payoff is high:
- Eliminates the "why did it continue?" mysteries
- Makes the system fully recoverable
- Adds audit trail for strict rigor
- Enables better observability and debugging

The risk is low:
- Phased approach means the system is usable during implementation
- FSM is additive, not a rewrite
- Agents don't change
- Old plans still work

**Start with Phase 1 this week.** Get the reducer and STATE.json working. Then the rest is incremental.

