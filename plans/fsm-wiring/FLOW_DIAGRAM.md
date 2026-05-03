# fsm-wiring — Flow Diagram

## Happy Path: team-flow with FSM wiring

```
/team-flow my-feature
        │
        ▼
[Startup Recovery]
        │  read STATE.json → present?
        ├─ yes → load state
        ├─ no  → read EVENTS.jsonl → replay?
        │         ├─ yes → reconstruct_state()
        │         └─ no  → State(IDLE)
        │  verify disk feedback vs state
        │  (disk wins if conflict)
        ▼
reduce(IDLE, CommandEvent)
        │  → STORMING
        │  EventLog.append + write_state_json
        ▼
spawn(architect)
        │
        ▼
reduce(STORMING, AgentDoneEvent("architect"))
        │  → STORM_PAUSED
        │  EventLog.append + write_state_json
        ▼
[PAUSE: human replies "yes"]
        │
        ▼
reduce(STORM_PAUSED, HumanResponseEvent("yes"))
reduce(_, StateTransitionEvent("PLANNING"))
        │  → PLANNING
        ▼
spawn(planner)
        │
        ▼
reduce(PLANNING, AgentDoneEvent("planner"))
        │  → PLAN_PAUSED
        ▼
[PAUSE: human replies "go"]
        │
        ▼
reduce(_, StateTransitionEvent("BUILDING"))
        │  → BUILDING
        ▼
spawn(builder) ← Conv N
        │
        ▼
[FSM Guards — run in order]
        │
        ├─ Guard 1: scan feedback/
        │     ├─ file exists?
        │     │     ├─ yes → reduce(_, FileCreatedEvent(file))
        │     │     │         route to responsible agent
        │     │     │         on delete: reduce(_, FileDeletedEvent)
        │     │     │         re-scan
        │     │     └─ no  → pass
        │
        ├─ Guard 2: retry_count_by_key check
        │     ├─ > 2?
        │     │     ├─ yes → write HUMAN_QUESTIONS.md
        │     │     │         reduce(_, FileCreatedEvent("HUMAN_QUESTIONS.md"))
        │     │     │         STOP
        │     │     └─ no  → reduce(_, SYSTEM_EVENT(RETRY, key))
        │     │               pass
        │
        └─ Guard 3: zero-diff check (REVIEW_FAILURES.md fix only)
              │  git diff HEAD -- . ":(exclude)plans/"
              ├─ empty  → reduce(_, NoDiffDetectedEvent)
              │             write HUMAN_QUESTIONS.md [STALL]
              │             STOP
              ├─ error  → log warning, pass
              └─ non-empty → pass
        │
        ▼
reduce(BUILDING, AgentDoneEvent("builder"))
        │  → REVIEWING
        ▼
spawn(reviewer)
        │
        ▼
reduce(REVIEWING, AgentDoneEvent("reviewer"))
        │  → IMPLEMENT_PAUSED
        ▼
[PAUSE: human replies "continue"]
        │
        ▼
[loop back to spawn(builder) for next Conv]
        │  (all convs done?)
        ▼
[Stage 4 Gate — read PROGRESS.md]
        │  any conv NOT DONE?
        ├─ yes → STOP, report incomplete conv
        └─ no  → reduce(_, ImplementCompleteEvent)
                   │  → TESTING
                   ▼
              spawn(tester)
                   │
                   ▼
              reduce(TESTING, AgentDoneEvent("tester"))
                   │  → TEST_PAUSED
                   ▼
              [PAUSE: human replies "done"]
                   │
                   ▼
              reduce(_, StateTransitionEvent("RETRO"))
                   ▼
              spawn(quick)
                   │
                   ▼
              reduce(RETRO, AgentDoneEvent("quick"))
                   │  → DONE
                   ▼
              write STATE.json (DONE)
```

## Feedback Routing Flow (Guard 1 Detail)

```
scan plans/<feature>/feedback/
        │
        ├─ HUMAN_QUESTIONS.md? → BLOCKED_ON_HUMAN → STOP
        ├─ ARCH_FEEDBACK.md?   → architect fixes → delete → re-scan
        ├─ DESIGN_QUESTIONS.md?→ architect fixes → delete → re-scan
        ├─ IMPL_QUESTIONS.md?  → planner fixes  → delete → re-scan
        ├─ REVIEW_FAILURES.md? → builder fixes  → Guard 3 → reviewer
        ├─ TEST_FAILURES.md?   → builder fixes  → delete → re-scan
        └─ (none)              → advance
```

## Retry Escalation Flow (Guard 2 Detail)

```
retry_count_by_key["conv-N:FILE.md"]
        │
        ├─ 0 → route fix agent, emit RETRY event → count = 1
        ├─ 1 → route fix agent, emit RETRY event → count = 2
        ├─ 2 → route fix agent, emit RETRY event → count = 3
        └─ 3 → STOP: write HUMAN_QUESTIONS.md
                      reduce(_, FileCreatedEvent("HUMAN_QUESTIONS.md"))
                      → BLOCKED_ON_HUMAN
```

## Component Legend

| Symbol | Meaning |
|--------|---------|
| `[Startup Recovery]` | Reads STATE.json, EVENTS.jsonl, or starts fresh |
| `reduce(state, event)` | Pure FSM function in orchestrator/reducer.py |
| `EventLog.append` | Writes one line to plans/<feature>/EVENTS.jsonl |
| `write_state_json` | Overwrites plans/<feature>/STATE.json |
| `[FSM Guards]` | Three checks run before every forward advance |
| `spawn(agent)` | Orchestrator creates a subagent for the named role |
| `[PAUSE]` | Human pause point; reply recorded as HumanResponseEvent |
