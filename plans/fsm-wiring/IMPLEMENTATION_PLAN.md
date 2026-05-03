# fsm-wiring — Implementation Plan

## Overview

Wire the existing `orchestrator/` FSM module into the `team-flow` skill so every decision point in the pipeline is a formal state transition. Phase 1 built the passive FSM (state, events, reducer, eventlog). Phase 2 activates it: `team-flow` reads state on startup, calls `reduce()` before each spawn, enforces retry guards and stall detection, and writes `STATE.json` + `EVENTS.jsonl` at every checkpoint.

No agent behavioral contracts change. No plan file formats change. Features without `STATE.json` continue to work.

## Layer Architecture

The `team-flow` skill is the orchestrator. It already instructs subagents. Phase 2 adds FSM calls alongside those instructions.

```
team-flow SKILL.md (prose orchestration rules)
     │  calls reduce() at each decision point
     ▼
orchestrator/reducer.py   ← pure reduce(state, event)
     │  returns new_state
     ▼
orchestrator/eventlog.py  ← append(event), write_state_json(state)
     │  reads/writes
     ▼
plans/<feature>/EVENTS.jsonl   ← append-only event log
plans/<feature>/STATE.json     ← current state snapshot
```

## Phases

### Phase 1: Startup Recovery + FSM Checkpoint Wiring (medium)
**Layer:** Orchestrator Skill (team-flow SKILL.md)
**Delivers stories:** S1.1, S1.2, S3.3

**Files:**
- `skills/team-flow/SKILL.md` — Add "FSM checkpoint protocol" section describing startup recovery and per-spawn checkpoint pattern. This is the authoritative prose that the orchestrator (LLM) reads and follows.

**Details:**

Add a new section to `team-flow` SKILL.md titled `## FSM checkpoint protocol` that instructs the orchestrator to:

1. **On startup** — before anything else:
   - If `plans/<feature>/STATE.json` exists: read it, log `Recovered state: <current> (from STATE.json)`. Verify against disk: if any feedback file exists but state is not `BLOCKED_*`, correct state and log the correction.
   - Else if `plans/<feature>/EVENTS.jsonl` exists: replay via `orchestrator/eventlog.py EventLog.reconstruct_state()`, log `Recovered state: <current> (from EVENTS.jsonl replay)`.
   - Else: start from `IDLE`, log `No prior state found — starting fresh`.
   - In `strict` rigor: if neither file exists, stop and report: `strict mode requires STATE.json. Run /team-flow <feature> build to initialize.`

2. **Before each agent spawn** — emit the correct event for the transition, call `reduce(current_state, event)`, then:
   - Call `EventLog.append(event)` to append to `plans/<feature>/EVENTS.jsonl`
   - Call `EventLog.write_state_json(new_state)` to update `plans/<feature>/STATE.json`
   - Then proceed to spawn the agent.

3. **Backward compatibility** — if `plans/<feature>/` does not exist yet (early discovery), create the directory before writing event files. If IO fails, log a warning but do not block the spawn.

**Verify:** `python -c "from orchestrator.eventlog import EventLog; from orchestrator.reducer import reconstruct; log = EventLog(feature='fsm-wiring'); log.reconstruct_state(); print('OK')"`

---

### Phase 2: Feedback Guard + Retry Enforcement + Stall Detection (medium)
**Layer:** Orchestrator Skill (team-flow SKILL.md)
**Delivers stories:** S1.3, S2.1, S2.2

**Files:**
- `skills/team-flow/SKILL.md` — Add prose for three guards that run at each build/review checkpoint

**Details:**

Add a `## FSM guards` section to `team-flow` SKILL.md with three numbered guards. Each runs in order before any forward advance:

**Guard 1 — Feedback-open check:**
- Scan `plans/<feature>/feedback/` for open files.
- If any exist: call `reduce(state, FileCreatedEvent(file=highest_priority_file))`, update logs.
- Route to the responsible agent per the priority order already in SKILL.md.
- When that agent resolves and deletes the file: call `reduce(state, FileDeletedEvent(file))`, update logs, re-scan.
- Only advance when no feedback files remain.

**Guard 2 — Retry-count check:**
- Before routing a feedback file to its responsible agent, check `state.retry_count_by_key["conv-N:FILE.md"]`.
- If the value is already `> 2`: do not spawn the agent. Instead, write `plans/<feature>/feedback/HUMAN_QUESTIONS.md` with escalation message, call `reduce(state, FileCreatedEvent("HUMAN_QUESTIONS.md"))`, update logs, stop.
- After routing (spawning the fix agent), call `reduce(state, SystemEvent(action="RETRY", retry_key="conv-N:FILE.md"))` and update logs so the counter increments.
- Exception: `IMPL_QUESTIONS.md` and `DESIGN_QUESTIONS.md` do not consume retry budget — they are clarification requests, not fix loops.

**Guard 3 — Zero-diff stall check (applies only after `REVIEW_FAILURES.md` fix):**
- After builder finishes a `REVIEW_FAILURES.md` fix, before re-spawning reviewer, run: `git diff HEAD -- . ":(exclude)plans/"`.
- If output is empty: call `reduce(state, NoDiffDetectedEvent())`, update logs. Write `HUMAN_QUESTIONS.md` with `[STALL]` tag. Stop and report: `Zero-diff loop detected for Conv N. Escalated to HUMAN_QUESTIONS.md.`
- If `git diff` fails (not a git repo): skip check, log warning, proceed.
- If output is non-empty: proceed to re-spawn reviewer.

**Verify:** Manual inspection — run `/team-flow fsm-wiring build` on a feature with a mock `REVIEW_FAILURES.md` in place and confirm the guard fires before builder spawns.

---

### Phase 3: All-Conversations Gate + Human Pause Events + PROGRESS.md Check (small)
**Layer:** Orchestrator Skill (team-flow SKILL.md)
**Delivers stories:** S3.1, S3.2

**Files:**
- `skills/team-flow/SKILL.md` — Add gate for Stage 4 entry and pause-point event recording

**Details:**

**Gate — before Stage 4 (Test):**
- Read `plans/<feature>/PROGRESS.md`, check every conversation row.
- If any row is not `DONE`: stop and report `Not all conversations are complete. Run /team-flow <feature> build first. Incomplete: Conv N`.
- When all are `DONE`: call `reduce(state, ImplementCompleteEvent())`, update logs; resulting state should be `TESTING`. Then spawn tester.

**Human pause events:**
- Each time the skill pauses and waits for user input, after the user replies:
  - If reply is a proceed signal ('yes', 'go', 'continue', 'done', numeric choice): call `reduce(state, HumanResponseEvent(value=reply))`, update logs, advance.
  - If reply is a stop signal ('no', 'stop'): call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, halt. `STATE.json` must be written before exit.
  - If reply is unrecognised: re-prompt without recording a `HUMAN_RESPONSE` event.
- In fast mode: record `HumanResponseEvent(value="auto-advance")` at each skipped pause so the log is coherent.

**Verify:** `python -c "from orchestrator.state import State; from orchestrator.events import ImplementCompleteEvent; from orchestrator.reducer import reduce; s = reduce(State(current='BUILDING'), ImplementCompleteEvent()); print(s.current)"` — should print `TESTING`.

---

## Prerequisites

- Phase 1 is complete: `orchestrator/state.py`, `orchestrator/events.py`, `orchestrator/reducer.py`, `orchestrator/eventlog.py` all exist and 9/9 unit tests pass
- `python -m pytest orchestrator/test_fsm.py -q` passes before this work begins
- `skills/team-flow/SKILL.md` is the only file to modify in Phase 2

## Key Decisions

- **Prose, not code, in SKILL.md** — The orchestrator is an LLM that reads SKILL.md. Phase 2 changes SKILL.md prose to instruct the LLM when and how to call the FSM Python module. No Python driver script is introduced in this phase.
- **Disk wins over state cache** — When `STATE.json` disagrees with feedback files on disk, disk is authoritative. `STATE.json` is corrected, not trusted blindly.
- **Retry keys scoped to conversation + file** — `conv-N:FILE.md` prevents retries in one conversation consuming budget for another.
- **Clarification requests exempt from retry budget** — `IMPL_QUESTIONS.md` and `DESIGN_QUESTIONS.md` are not fix loops; they never increment retry counters.
