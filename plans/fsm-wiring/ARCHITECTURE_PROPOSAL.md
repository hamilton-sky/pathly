# fsm-wiring — Architecture Proposal

## Problem Statement

The `team-flow` skill currently makes every pipeline decision from prose rules in SKILL.md. State is implicit — inferred from agent memory and file presence. The `orchestrator/` FSM module exists (Phase 1 complete) but is never called. Phase 2 must activate it: every decision point becomes a formal event → transition → log cycle, without changing any agent, any plan file format, or any user-facing command.

## Proposed Solution

Add two new prose sections to `skills/team-flow/SKILL.md`:

1. `## FSM checkpoint protocol` — instructs the orchestrator LLM when and how to call the FSM Python module at startup and before each spawn.
2. `## FSM guards` — instructs the orchestrator LLM to run three mechanical checks (feedback-open, retry-count, zero-diff) before any forward advance.

Additionally, amend Stage 4 with a PROGRESS.md gate and amend each pause block to record `HumanResponseEvent`.

No new Python files. No changes to `orchestrator/*.py`. No changes to agents, other skills, or plan templates.

## Component Map

```
skills/team-flow/SKILL.md  (this file changes)
     │  reads
     ▼
orchestrator/eventlog.py   EventLog
     │  uses
     ├─► orchestrator/reducer.py    reduce()
     ├─► orchestrator/state.py      State
     └─► orchestrator/events.py     *Event classes

     │  reads/writes
     ▼
plans/<feature>/
  ├── STATE.json      ← current state snapshot
  └── EVENTS.jsonl   ← append-only audit log
```

## Key Design Decisions

### Decision 1: Prose-Only Change — No Python Driver Script
- **Options considered**: (A) Add a Python driver script that SKILL.md calls via subprocess, (B) Add FSM calls as prose instructions in SKILL.md only
- **Chosen**: B — prose only
- **Rationale**: The orchestrator is an LLM reading SKILL.md. Adding a driver script would require the LLM to invoke it correctly via bash, adding failure modes. Prose instructions are the native contract. The Python module (`orchestrator/`) is already designed to be called directly by the orchestrator LLM via tool use. Keeping Phase 2 in prose means no new infrastructure, no subprocess wiring, and no new failure modes.

### Decision 2: Disk Wins Over STATE.json Cache
- **Options considered**: (A) Trust `STATE.json` as authoritative, (B) Always replay from `EVENTS.jsonl`, (C) Disk feedback files win; STATE.json is a fast-path cache
- **Chosen**: C
- **Rationale**: `STATE.json` can become stale if the pipeline crashed mid-write. Feedback files on disk are ground truth — they exist or they don't, with no partial-write risk. Using disk-wins prevents silent inconsistencies. `EVENTS.jsonl` is the audit trail; `STATE.json` is just a read-optimisation.

### Decision 3: Retry Keys Scoped to (Conversation, File)
- **Options considered**: (A) Single global retry counter, (B) Per-file retry counter, (C) Per-(conversation, file) retry counter
- **Chosen**: C — key format `"conv-N:FILE.md"`
- **Rationale**: A global counter would block Conv 2 if Conv 1 had two retries. A per-file counter would conflate retries across conversations. The per-(conversation, file) key is the finest grain that still prevents infinite loops while not penalising independent feedback cycles.

### Decision 4: IMPL_QUESTIONS.md and DESIGN_QUESTIONS.md Exempt From Retry Budget
- **Options considered**: (A) Count all feedback files in retry budget, (B) Exempt clarification-request files
- **Chosen**: B
- **Rationale**: Clarification requests (`IMPL_QUESTIONS.md`, `DESIGN_QUESTIONS.md`) are not fix loops — they represent legitimate ambiguity in the spec or design. Charging retry budget to them would wrongly penalise builders for asking good questions. Fix loops (`REVIEW_FAILURES.md`, `TEST_FAILURES.md`) are the actual failure mode to detect.

### Decision 5: Zero-Diff Exclusion Pattern `:(exclude)plans/`
- **Options considered**: (A) `git diff HEAD`, (B) `git diff HEAD -- .`, (C) `git diff HEAD -- . ":(exclude)plans/"`
- **Chosen**: C
- **Rationale**: A builder might legitimately update plan files (e.g. PROGRESS.md) without touching implementation code. Option A and B would see this as a non-empty diff and miss the stall. Excluding the `plans/` tree isolates the diff to implementation files only, which is the true stall signal.

## New Sections in SKILL.md

```
## FSM checkpoint protocol     ← NEW (Conv 1)
## FSM guards                  ← NEW (Conv 2)
## Health checks before skipping stages   ← EXISTING (unchanged)
## Feedback file locations                ← EXISTING (unchanged)
...
## Stage 4 — Test + Fix Loop              ← EXISTING (amended Conv 3)
  [PROGRESS.md pre-gate added at top]
[Each pause block]                        ← EXISTING (amended Conv 3)
  [HumanResponseEvent recording added]
```

## Event Emission Map

| Pipeline moment | Event emitted | Resulting state |
|---|---|---|
| `/team-flow` invoked | `CommandEvent` | `STORMING` |
| Architect done | `AgentDoneEvent(agent="architect")` | `STORM_PAUSED` |
| Human replies 'yes' at storm pause | `HumanResponseEvent("yes")` | — |
| Advancing to plan | `StateTransitionEvent(to_state="PLANNING")` | `PLANNING` |
| Planner done | `AgentDoneEvent(agent="planner")` | `PLAN_PAUSED` |
| Human replies 'go' at plan pause | `HumanResponseEvent("go")` | — |
| Advancing to build | `StateTransitionEvent(to_state="BUILDING")` | `BUILDING` |
| Builder done | `AgentDoneEvent(agent="builder")` | `REVIEWING` |
| Feedback file found | `FileCreatedEvent(file=...)` | `BLOCKED_ON_FEEDBACK` |
| Feedback file resolved | `FileDeletedEvent(file=...)` | `previous_state` |
| Retry counted | `SystemEvent(action="RETRY", retry_key=...)` | unchanged |
| Zero diff detected | `NoDiffDetectedEvent` | `BLOCKED_ON_HUMAN` |
| Reviewer done | `AgentDoneEvent(agent="reviewer")` | `IMPLEMENT_PAUSED` |
| All conversations done | `ImplementCompleteEvent` | `TESTING` |
| Tester done | `AgentDoneEvent(agent="tester")` | `TEST_PAUSED` |
| Quick (retro) done | `AgentDoneEvent(agent="quick")` | `DONE` |

## Risks

- **LLM drift**: The orchestrator is an LLM and may skip a checkpoint under context pressure. Mitigation: `## FSM checkpoint protocol` and `## FSM guards` are explicit, numbered instructions. Phase 4 (audit verification) will add a `/verify-state` command to detect drift.
- **STATE.json stale after crash**: Mid-write crash leaves STATE.json partially written. Mitigation: disk-wins rule (EC-1.2). The next startup corrects the state from feedback files.
- **Slow replay on large EVENTS.jsonl**: Long pipelines accumulate many events; `reconstruct_state()` replays all of them. Mitigation: `STATE.json` is read first as a fast path; replay is the fallback. Snapshotting is a Phase 4 concern.
