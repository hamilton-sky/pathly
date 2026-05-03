# fsm-wiring — Happy Flow

## Overview

The ideal scenario is a standard two-conversation feature running through the full `team-flow` pipeline with FSM wiring active. Every agent spawn is preceded by a `reduce()` call, every checkpoint writes to `EVENTS.jsonl` and `STATE.json`, and no feedback files are open at any decision point. The pipeline runs cleanly from discovery to retro.

## Step-by-Step Happy Flow

### Step 1: Startup — State Recovery
- **Action**: `/team-flow my-feature` is invoked
- **Orchestrator does**: Reads `plans/my-feature/STATE.json` — finds it absent (first run). Checks `plans/my-feature/EVENTS.jsonl` — also absent. Initialises `State(current="IDLE")`. Creates `plans/my-feature/` directory if needed.
- **Outcome**: Logs `No prior state found — starting fresh`. State is `IDLE`.

### Step 2: Command Event + Storm
- **Action**: Orchestrator processes the `/team-flow` command as a `COMMAND` event
- **Orchestrator does**: Calls `reduce(IDLE, CommandEvent(feature="my-feature", rigor="standard", mode="interactive"))`. Result: `STORMING`. Calls `EventLog.append(event)` and `EventLog.write_state_json(STORMING)`. Spawns `architect`.
- **Outcome**: `STATE.json` shows `STORMING`. `EVENTS.jsonl` has one line.

### Step 3: Architect Done → Plan
- **Action**: Architect finishes storm
- **Orchestrator does**: Calls `reduce(STORMING, AgentDoneEvent(agent="architect"))`. Result: `STORM_PAUSED`. Updates logs. Pauses for human input.
- **Human replies**: 'yes' — orchestrator calls `reduce(STORM_PAUSED, HumanResponseEvent("yes"))`, updates logs. Calls `reduce(_, StateTransitionEvent(to_state="PLANNING"))`, spawns `planner`.
- **Outcome**: `STATE.json` shows `PLANNING`.

### Step 4: Plan Done → Build
- **Action**: Planner finishes plan files
- **Orchestrator does**: Calls `reduce(PLANNING, AgentDoneEvent(agent="planner"))`. Result: `PLAN_PAUSED`. Pauses for human.
- **Human replies**: 'go' — orchestrator records `HumanResponseEvent("go")`, transitions to `BUILDING`, spawns `builder` for Conv 1.
- **Outcome**: `STATE.json` shows `BUILDING`.

### Step 5: Builder Done — FSM Guards Run
- **Action**: Builder completes Conv 1
- **Orchestrator does**:
  1. Scans `plans/my-feature/feedback/` — empty. Guard 1 passes.
  2. No retry key to check. Guard 2 passes.
  3. Guard 3 not applicable (not a REVIEW_FAILURES.md fix).
  4. Calls `reduce(BUILDING, AgentDoneEvent(agent="builder"))`. Result: `REVIEWING`.
  5. Updates logs. Spawns `reviewer`.
- **Outcome**: `STATE.json` shows `REVIEWING`.

### Step 6: Reviewer Passes
- **Action**: Reviewer finds no violations — reports PASS
- **Orchestrator does**: Calls `reduce(REVIEWING, AgentDoneEvent(agent="reviewer"))`. Result: `IMPLEMENT_PAUSED`. Pauses for human.
- **Human replies**: 'continue' — orchestrator records event, transitions back to `BUILDING` for Conv 2, spawns builder.
- **Outcome**: `STATE.json` shows `BUILDING`.

### Step 7: All Conversations Done — Gate Before Test
- **Action**: Builder completes Conv 2 (last conversation)
- **Orchestrator does**: Reviewer runs and passes. Orchestrator checks `PROGRESS.md` — all conversation rows are `DONE`. Calls `reduce(BUILDING, ImplementCompleteEvent())`. Result: `TESTING`. Spawns `tester`.
- **Outcome**: `STATE.json` shows `TESTING`.

### Step 8: Tester Passes → Retro
- **Action**: Tester verifies all acceptance criteria — no `TEST_FAILURES.md`
- **Orchestrator does**: Calls `reduce(TESTING, AgentDoneEvent(agent="tester"))`. Result: `TEST_PAUSED`. Human replies 'done'. Orchestrator records event, transitions to `RETRO`, spawns `quick`.
- **Outcome**: `STATE.json` shows `RETRO`.

### Step 9: Retro → Done
- **Action**: Quick agent writes `RETRO.md`
- **Orchestrator does**: Calls `reduce(RETRO, AgentDoneEvent(agent="quick"))`. Result: `DONE`. Updates logs.
- **Outcome**: `STATE.json` shows `DONE`. `EVENTS.jsonl` has a complete audit trail.

## End State

- `plans/my-feature/STATE.json` — `{ "current": "DONE", ... }`
- `plans/my-feature/EVENTS.jsonl` — one line per event: COMMAND, AGENT_DONE (architect), HUMAN_RESPONSE, AGENT_DONE (planner), HUMAN_RESPONSE, AGENT_DONE (builder), AGENT_DONE (reviewer), HUMAN_RESPONSE, AGENT_DONE (builder), AGENT_DONE (reviewer), IMPLEMENT_COMPLETE, AGENT_DONE (tester), HUMAN_RESPONSE, AGENT_DONE (quick)
- All plan files in `plans/my-feature/` unchanged
- No feedback files remain

## Success Indicators

- [ ] `STATE.json` exists after the first agent spawn
- [ ] `EVENTS.jsonl` line count equals number of events emitted (no missing checkpoints)
- [ ] `STATE.json` shows `DONE` at pipeline completion
- [ ] No feedback files remain in `plans/my-feature/feedback/`
- [ ] `python -m pytest orchestrator/test_fsm.py -q` still passes after all conversations
