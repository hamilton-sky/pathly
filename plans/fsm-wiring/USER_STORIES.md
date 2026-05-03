# fsm-wiring — User Stories

## Context

The `orchestrator/` Python module (Phase 1) ships a complete FSM: state, events, reducer, and eventlog. But it is passive — the `team-flow` skill currently ignores it and makes every pipeline decision from prose rules in SKILL.md.

Phase 2 makes the FSM active. Every decision point in the `team-flow` skill is now a formal state transition: the skill calls `reduce(state, event)` before spawning any agent, appends to `EVENTS.jsonl`, and writes `STATE.json`. Rules that were advisory ("max 2 retries") become enforced. Stall loops that required manual detection become automatic.

Features that have no `STATE.json` or `EVENTS.jsonl` continue to work unchanged. The FSM is additive infrastructure.

---

## Stories

### Story 1.1: Startup State Recovery
**As a** pipeline operator, **I want** `team-flow` to read `STATE.json` and `EVENTS.jsonl` on startup, **so that** resuming an interrupted pipeline restores the exact state rather than re-inferring it from memory.

**Acceptance Criteria:**
- [ ] When `plans/<feature>/STATE.json` exists, `team-flow` loads it and logs: `Recovered state: <current> (from STATE.json)`
- [ ] When `STATE.json` is absent but `EVENTS.jsonl` exists, `team-flow` replays events via `EventLog.reconstruct_state()` and logs: `Recovered state: <current> (from EVENTS.jsonl replay)`
- [ ] When neither file exists, `team-flow` starts from `IDLE` with no error
- [ ] If disk feedback files contradict `STATE.json` (e.g. `HUMAN_QUESTIONS.md` exists but state is `BUILDING`), disk wins and the state is corrected to `BLOCKED_ON_HUMAN`
- [ ] After recovery, `STATE.json` and `EVENTS.jsonl` reflect the corrected state

**Edge Cases:**
- `STATE.json` is corrupt JSON → fall back to `EVENTS.jsonl` replay; if that also fails, start from `IDLE` and warn
- `EVENTS.jsonl` contains an unknown event type → skip that line and continue replay

**Delivered by:** Phase 1 → Conversation 1

---

### Story 1.2: FSM Checkpoint Before Agent Spawn
**As a** pipeline operator, **I want** `team-flow` to call `reduce(state, event)` before spawning any agent, **so that** every spawn is a recorded state transition rather than an invisible side-effect.

**Acceptance Criteria:**
- [ ] Before spawning `builder`, the skill emits an `AGENT_DONE` or `STATE_TRANSITION` event and calls `reduce()`; the resulting state is `BUILDING`
- [ ] Before spawning `reviewer`, the skill emits the preceding event and calls `reduce()`; resulting state is `REVIEWING`
- [ ] Before spawning any other agent (`architect`, `planner`, `tester`, `quick`), the skill does the same pattern
- [ ] After each `reduce()` call, `EventLog.append(event)` is called and `EventLog.write_state_json(new_state)` is written
- [ ] `plans/<feature>/EVENTS.jsonl` and `plans/<feature>/STATE.json` exist and are up-to-date after every agent spawn

**Edge Cases:**
- Feature plan directory does not exist yet (discovery stage) → create it before writing event files
- `EventLog.append()` raises an IO error → log warning, do not block the spawn

**Delivered by:** Phase 1 → Conversation 1

---

### Story 1.3: Feedback-Open Guard
**As a** pipeline operator, **I want** `team-flow` to consult the FSM before any forward advance, **so that** it never spawns the next agent when a feedback file is still open.

**Acceptance Criteria:**
- [ ] Before advancing past any build/review checkpoint, the skill scans `plans/<feature>/feedback/` for open files
- [ ] If any feedback file exists, `reduce(state, FILE_CREATED(file))` is called; resulting state is `BLOCKED_ON_FEEDBACK` or `BLOCKED_ON_HUMAN`
- [ ] The skill routes to the correct responsible agent according to the priority order defined in SKILL.md: `HUMAN_QUESTIONS.md` first, then `ARCH_FEEDBACK.md`, `DESIGN_QUESTIONS.md`, `IMPL_QUESTIONS.md`, `REVIEW_FAILURES.md`, `TEST_FAILURES.md`
- [ ] Only one feedback file is routed at a time; the others remain on disk
- [ ] When the responsible agent deletes the feedback file, `reduce(state, FILE_DELETED(file))` is called; state returns to `previous_state`

**Edge Cases:**
- Multiple feedback files exist simultaneously → priority order is enforced strictly; lowest-priority files are untouched
- Feedback file is deleted by a non-agent process (manual cleanup) → next checkpoint scan sees no file and advances normally

**Delivered by:** Phase 2 → Conversation 2

---

### Story 2.1: Retry-Count Enforcement
**As a** pipeline operator, **I want** the FSM to track retry counts per `(conversation, feedback-file)` pair, **so that** a looping feedback cycle is detected and escalated after two attempts rather than spinning forever.

**Acceptance Criteria:**
- [ ] Each time a feedback file is re-opened for the same conversation, `reduce(state, SYSTEM_EVENT(RETRY, retry_key="conv-N:FILE.md"))` is called
- [ ] `state.retry_count_by_key["conv-N:FILE.md"]` increments with each retry event
- [ ] When `retry_count_by_key["conv-N:FILE.md"] > 2`, the skill stops the loop and writes `plans/<feature>/feedback/HUMAN_QUESTIONS.md` with the escalation message: `Feedback loop exceeded for Conv N (FILE.md). Manual intervention required.`
- [ ] After writing `HUMAN_QUESTIONS.md`, the FSM state transitions to `BLOCKED_ON_HUMAN`
- [ ] Retry budgets are independent per key — Conv 1 retries do not consume Conv 2's budget

**Edge Cases:**
- `retryCount` check happens before spawning the fix agent, not after
- A conversation with no feedback file never increments any retry key

**Delivered by:** Phase 2 → Conversation 2

---

### Story 2.2: Zero-Diff Stall Detection
**As a** pipeline operator, **I want** `team-flow` to detect when a builder claims to have fixed violations but produced no code change, **so that** zero-diff stall loops escalate to human review automatically rather than looping indefinitely.

**Acceptance Criteria:**
- [ ] After builder completes a `REVIEW_FAILURES.md` fix, the skill runs `git diff HEAD -- . ":(exclude)plans/"` before re-spawning the reviewer
- [ ] If the diff output is empty, `reduce(state, NO_DIFF_DETECTED())` is called; resulting state is `BLOCKED_ON_HUMAN`
- [ ] The skill writes `plans/<feature>/feedback/HUMAN_QUESTIONS.md` with `[STALL]` tag and the original `REVIEW_FAILURES.md` content
- [ ] The skill stops and reports: `Zero-diff loop detected for Conv N. Escalated to HUMAN_QUESTIONS.md — manual intervention required.`
- [ ] If the diff is non-empty, the skill proceeds normally to re-spawn reviewer

**Edge Cases:**
- Builder deletes `REVIEW_FAILURES.md` but changes only plan files (not implementation files) → diff of `":(exclude)plans/"` is still empty → stall is correctly detected
- `git diff` fails (not a git repo) → skip stall check, log warning, proceed normally

**Delivered by:** Phase 2 → Conversation 2

---

### Story 3.1: All-Conversations-Done Gate Before Test
**As a** pipeline operator, **I want** `team-flow` to verify all conversations are DONE in PROGRESS.md before entering Stage 4, **so that** incomplete implementation never reaches the test stage.

**Acceptance Criteria:**
- [ ] Before spawning `tester`, the skill reads `plans/<feature>/PROGRESS.md` and checks every conversation row
- [ ] If any conversation row is not `DONE`, the skill stops and reports: `Not all conversations are complete. Run /team-flow <feature> build first. Incomplete: Conv N`
- [ ] When all conversations are `DONE`, `reduce(state, IMPLEMENT_COMPLETE())` is called; resulting state is `TESTING`
- [ ] `STATE.json` reflects `TESTING` before `tester` is spawned

**Edge Cases:**
- `PROGRESS.md` is missing or cannot be parsed → stop and report rather than proceeding to test

**Delivered by:** Phase 3 → Conversation 3

---

### Story 3.2: Human Pause Points as FSM Events
**As a** pipeline operator, **I want** every human pause-point acknowledgement to be recorded as a `HUMAN_RESPONSE` event, **so that** the audit log captures the full decision trail including operator approvals.

**Acceptance Criteria:**
- [ ] When the operator replies to a pause prompt (e.g. 'go', 'yes', 'continue', 'done'), the skill emits `reduce(state, HUMAN_RESPONSE(value))` before advancing
- [ ] The event is appended to `EVENTS.jsonl` with the human's response value
- [ ] When the operator replies 'no' or 'stop', `reduce(state, HUMAN_RESPONSE("stop"))` is called and the pipeline halts; `STATE.json` is written before exit
- [ ] Fast mode skips pause points but still records `HUMAN_RESPONSE("auto-advance")` events so the log remains coherent

**Edge Cases:**
- Operator types an unrecognised response → skill re-prompts without recording a `HUMAN_RESPONSE` event

**Delivered by:** Phase 3 → Conversation 3

---

### Story 3.3: Backward Compatibility — Features Without STATE.json
**As a** pipeline operator, **I want** `team-flow` to work normally for features that have no `STATE.json` or `EVENTS.jsonl`, **so that** existing in-progress features are not broken by the Phase 2 changes.

**Acceptance Criteria:**
- [ ] If `plans/<feature>/STATE.json` does not exist, `team-flow` initialises a fresh `State()` and proceeds without error
- [ ] If `plans/<feature>/EVENTS.jsonl` does not exist, `EventLog.read_all()` returns an empty list without raising
- [ ] The first write to `plans/<feature>/EVENTS.jsonl` creates the file automatically
- [ ] In `lite` and `standard` rigor, a missing `STATE.json` is not an error; in `strict`, it is flagged at the health check

**Edge Cases:**
- `plans/<feature>/` directory exists but is empty → same as no state files; initialise fresh

**Delivered by:** Phase 1 → Conversation 1
