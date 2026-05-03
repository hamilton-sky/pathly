# fsm-wiring — Conversation Guide

Split into 3 conversations (max 4). Each produces a runnable, testable change to `skills/team-flow/SKILL.md`.
After each conversation, **commit your changes** before starting the next.

---

## Conversation 1: Startup Recovery + FSM Checkpoint Wiring (Phase 1)

**Stories delivered:** S1.1, S1.2, S3.3

**Prompt to paste:**
```
Implement fsm-wiring Conversation 1 (Phase 1) from plans/fsm-wiring/IMPLEMENTATION_PLAN.md.

Phase 1 objective: Add an "FSM checkpoint protocol" section to `skills/team-flow/SKILL.md` that instructs the orchestrator (LLM) when and how to consult the existing `orchestrator/` Python module at each decision point.

Scope:
- Add a new section `## FSM checkpoint protocol` to `skills/team-flow/SKILL.md` (insert after `## Core rules`, before `## Health checks before skipping stages`).
- The section must describe these three behaviours:
  1. On startup recovery: read STATE.json → fall back to EVENTS.jsonl replay → fall back to IDLE. Correct state if disk feedback files contradict STATE.json (disk wins). Log the recovery outcome. In strict rigor: if neither file exists, stop and report.
  2. Before each agent spawn: emit the correct event for the transition, call reduce(state, event) using orchestrator/reducer.py, then call EventLog.append(event) and EventLog.write_state_json(new_state) using orchestrator/eventlog.py, then spawn.
  3. Backward compatibility: if plans/<feature>/ does not exist yet, create it before writing. If IO fails, log warning but do not block spawn. Missing STATE.json or EVENTS.jsonl is not an error in lite or standard rigor.
- Reference specific class and method names from the existing codebase: EventLog (orchestrator/eventlog.py), reconstruct_state(), append(), write_state_json(); State (orchestrator/state.py); reduce() (orchestrator/reducer.py).
- Do NOT touch any other section of SKILL.md.
- Do NOT touch orchestrator/*.py — those files are DONE from Phase 1.
- Do NOT touch any agent files (agents/), other skills, or plan files.

Verify:
python -c "from orchestrator.eventlog import EventLog; from orchestrator.reducer import reconstruct; log = EventLog(feature='fsm-wiring'); log.reconstruct_state(); print('OK')"

This must print OK without error. It confirms the eventlog and reducer modules are importable and functional.

Also verify SKILL.md contains the new section by reading it and confirming the heading `## FSM checkpoint protocol` appears.

After done, update plans/fsm-wiring/PROGRESS.md: set Conv 1 to DONE, set stories S1.1, S1.2, S3.3 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** `skills/team-flow/SKILL.md` has a new `## FSM checkpoint protocol` section. Python verify command prints `OK`. PROGRESS.md updated.
**Files touched:** `skills/team-flow/SKILL.md`, `plans/fsm-wiring/PROGRESS.md`

---

## Conversation 2: Feedback Guard + Retry Enforcement + Stall Detection (Phase 2)

**Stories delivered:** S1.3, S2.1, S2.2

**Conversations 1 is DONE** (startup recovery + FSM checkpoint wiring in SKILL.md).

**Prompt to paste:**
```
Implement fsm-wiring Conversation 2 (Phase 2) from plans/fsm-wiring/IMPLEMENTATION_PLAN.md.

Phase 2 objective: Add an "FSM guards" section to `skills/team-flow/SKILL.md` with three guards that the orchestrator must run in order before any forward advance in the pipeline.

Scope:
- Add a new section `## FSM guards` to `skills/team-flow/SKILL.md` (insert after `## FSM checkpoint protocol`, before `## Health checks before skipping stages`).
- The section must define exactly three guards, applied in order:

  Guard 1 — Feedback-open check:
  - Scan plans/<feature>/feedback/ for open files.
  - If any exist: call reduce(state, FileCreatedEvent(file=highest_priority_file)), update logs.
  - Route to responsible agent per existing priority order (HUMAN_QUESTIONS.md first, then ARCH_FEEDBACK.md, DESIGN_QUESTIONS.md, IMPL_QUESTIONS.md, REVIEW_FAILURES.md, TEST_FAILURES.md).
  - When agent resolves and deletes file: call reduce(state, FileDeletedEvent(file)), update logs, re-scan.
  - Only advance when no feedback files remain.

  Guard 2 — Retry-count check:
  - Before routing a feedback file, check state.retry_count_by_key["conv-N:FILE.md"].
  - If > 2: write HUMAN_QUESTIONS.md with escalation message, call reduce(state, FileCreatedEvent("HUMAN_QUESTIONS.md")), update logs, stop.
  - After routing fix agent: call reduce(state, SystemEvent(action="RETRY", retry_key="conv-N:FILE.md")), update logs.
  - IMPL_QUESTIONS.md and DESIGN_QUESTIONS.md are exempt — they do not increment the retry counter.

  Guard 3 — Zero-diff stall check (after REVIEW_FAILURES.md fix only):
  - After builder finishes REVIEW_FAILURES.md fix, before re-spawning reviewer, run: git diff HEAD -- . ":(exclude)plans/"
  - If empty: call reduce(state, NoDiffDetectedEvent()), update logs. Write HUMAN_QUESTIONS.md with [STALL] tag. Stop and report: "Zero-diff loop detected for Conv N. Escalated to HUMAN_QUESTIONS.md."
  - If git diff fails (not a git repo): skip check, log warning, proceed.
  - If non-empty: proceed to reviewer.

- Reference exact class names: FileCreatedEvent, FileDeletedEvent, SystemEvent, NoDiffDetectedEvent (all from orchestrator/events.py). State.retry_count_by_key (orchestrator/state.py). reduce() (orchestrator/reducer.py).
- Do NOT touch any section of SKILL.md outside the new `## FSM guards` section.
- Do NOT touch orchestrator/*.py.
- Do NOT touch any agent files, other skills, or plan files.

Verify:
Read skills/team-flow/SKILL.md and confirm:
1. Section `## FSM guards` exists with Guard 1, Guard 2, Guard 3 headings.
2. Guard 2 references retry_count_by_key and the > 2 threshold.
3. Guard 3 references NoDiffDetectedEvent and the [STALL] tag.

After done, update plans/fsm-wiring/PROGRESS.md: set Conv 2 to DONE, set stories S1.3, S2.1, S2.2 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** `skills/team-flow/SKILL.md` has a new `## FSM guards` section with three guards. PROGRESS.md updated.
**Files touched:** `skills/team-flow/SKILL.md`, `plans/fsm-wiring/PROGRESS.md`

---

## Conversation 3: All-Conversations Gate + Human Pause Events (Phase 3)

**Stories delivered:** S3.1, S3.2

**Conversations 1-2 are DONE** (FSM checkpoint protocol + FSM guards in SKILL.md).

**Prompt to paste:**
```
Implement fsm-wiring Conversation 3 (Phase 3) from plans/fsm-wiring/IMPLEMENTATION_PLAN.md.

Phase 3 objective: Add two remaining FSM behaviours to `skills/team-flow/SKILL.md`: (1) a gate before Stage 4 that enforces all conversations are DONE before testing begins, and (2) recording of human pause-point responses as HUMAN_RESPONSE events.

Scope:
- In the existing `## Stage 4 — Test + Fix Loop` section of SKILL.md: add a pre-gate check at the top of the stage. Before spawning tester:
  1. Read plans/<feature>/PROGRESS.md and check every conversation row.
  2. If any row is not DONE: stop and report "Not all conversations are complete. Run /team-flow <feature> build first. Incomplete: Conv N".
  3. When all DONE: call reduce(state, ImplementCompleteEvent()), update logs (resulting state: TESTING), then spawn tester.

- In each existing pause-point block (Stage 1 pause, Stage 2 pause, Stage 3 advance pause, Stage 4 pause):
  - After user replies with a proceed signal ('yes', 'go', 'continue', 'done', numeric choice): call reduce(state, HumanResponseEvent(value=reply)), update logs, then advance.
  - After user replies with a stop signal ('no', 'stop'): call reduce(state, HumanResponseEvent(value="stop")), update logs, write STATE.json, halt.
  - If reply is unrecognised: re-prompt without recording a HUMAN_RESPONSE event.
  - In fast mode: record HumanResponseEvent(value="auto-advance") at each skipped pause.

- Reference exact class names: ImplementCompleteEvent, HumanResponseEvent (from orchestrator/events.py). reduce() (orchestrator/reducer.py). EventLog.append(), EventLog.write_state_json() (orchestrator/eventlog.py).
- Do NOT touch `## FSM checkpoint protocol` or `## FSM guards` sections added in Conv 1-2.
- Do NOT touch orchestrator/*.py.
- Do NOT touch any agent files, other skills, or plan files.

Verify:
python -c "from orchestrator.state import State; from orchestrator.events import ImplementCompleteEvent; from orchestrator.reducer import reduce; s = reduce(State(current='BUILDING'), ImplementCompleteEvent()); print(s.current)"

Must print: TESTING

Also read skills/team-flow/SKILL.md and confirm Stage 4 now has a PROGRESS.md pre-gate before tester is spawned, and that at least one pause block references HumanResponseEvent.

After done, update plans/fsm-wiring/PROGRESS.md: set Conv 3 to DONE, set stories S3.1 and S3.2 to DONE. Also set overall Status to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** `skills/team-flow/SKILL.md` Stage 4 has a PROGRESS.md gate. Pause blocks record `HumanResponseEvent`. Python verify prints `TESTING`. PROGRESS.md updated to DONE.
**Files touched:** `skills/team-flow/SKILL.md`, `plans/fsm-wiring/PROGRESS.md`
