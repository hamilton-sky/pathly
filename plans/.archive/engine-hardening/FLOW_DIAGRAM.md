# engine-hardening — Flow Diagram

## Change flow by layer

```
User input (feature name)
        │
        ▼
  DriverConfig.__post_init__          ← Conv 1 (S2)
  validate: no "..", "/", "\"
        │ ValueError if unsafe
        │ OK → continue
        ▼
  TeamFlowDriver._pre_flight()
  runner.is_available()               ← Conv 1 (S1)
        │ timeout=5s; TimeoutExpired → False
        │ False → print error, return False
        │ True → continue
        ▼
  TeamFlowDriver._run_agent(required)
        │                             ← Conv 2 (S3)
        ├─ exit=0  → emit AgentDoneEvent → advance FSM
        ├─ exit≠0, required=True  → sys.exit(1)
        └─ exit≠0, required=False → log WARN + emit AgentDoneEvent → advance FSM

## FSM state-stack nesting (Conv 4 tests verify this path)

  BUILDING
      │  FILE_CREATED(REVIEW_FAILURES)
      ▼
  BLOCKED_ON_FEEDBACK  [stack: BUILDING]
      │  FILE_CREATED(HUMAN_QUESTIONS)
      ▼
  BLOCKED_ON_HUMAN     [stack: BUILDING, BLOCKED_ON_FEEDBACK]
      │  FILE_DELETED(HUMAN_QUESTIONS)
      ▼
  BLOCKED_ON_FEEDBACK  [stack: BUILDING]
      │  FILE_DELETED(REVIEW_FAILURES)
      ▼
  BUILDING             [stack: empty]

## E2E test flow (Conv 3)

  tmp_path (git init)
      │
  write 4 core plan files
      │
  SuccessRunner (mock, always exit=0)
      │
  TeamFlowDriver(mode=FAST, entry=build)
      │
  driver.run()
      ├── BUILDING → AgentDoneEvent → IMPLEMENT_PAUSED
      ├── all_conversations_done()=True → ImplementCompleteEvent → TESTING
      ├── TESTING → AgentDoneEvent → TEST_PAUSED
      ├── TEST_PAUSED (fast) → RETRO
      └── RETRO → AgentDoneEvent → DONE
      │
  Assert: STATE.json current=DONE, EVENTS.jsonl has AGENT_DONE events
```
