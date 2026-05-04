---
name: team-flow
description: Full feature pipeline with feedback loops — discovery → plan → (implement → review → fix?) × N → test → (fix?) → retro. Standard/strict review every conversation; lite can review final-only. Feedback files route issues to the right agent automatically. Add 'lite', 'standard', or 'strict' to choose rigor. Add 'fast' to skip pause points outside strict mode. Add 'build', 'plan', or 'test' to enter mid-pipeline.
argument-hint: "<feature-name> [lite|standard|strict] [fast] [plan|build|test]"
---

Run the full feature pipeline for `$ARGUMENTS`.

## Argument parsing

Parse `$ARGUMENTS` for these tokens (order doesn't matter):
- First word that is not a keyword = `FEATURE` (the feature name)
- `lite` → set `rigor = lite` (4 required plan files, fewer gates)
- `standard` → set `rigor = standard` (default current pipeline)
- `strict` → set `rigor = strict` (mandatory gates, audit logs)
- `fast` → set `autoFlow = true` (no pause points)
- `plan` → set `entryStage = plan`
- `build` → set `entryStage = build`
- `test` → set `entryStage = test`
- Default: `entryStage = discovery`
- Default: `rigor = standard`

If both `strict` and `fast` are present, stop and report:
`strict mode requires human approval gates; remove fast or choose standard fast.`

Examples:
```
/team-flow hotel-search              ← full pipeline, path selector
/team-flow hotel-search build        ← skip to build stage
/team-flow hotel-search test         ← skip to test stage
/team-flow hotel-search fast         ← full pipeline, no pauses
/team-flow hotel-search build fast   ← resume build, no pauses
/team-flow hotel-search lite         ← small change, 4-file plan, lighter gates
/team-flow hotel-search strict       ← high-risk change, mandatory gates + audit
```

## Core rules

- Spawn the right subagent for each stage — never execute work yourself.
- Treat `/team-flow` as a deterministic filesystem FSM. Before each action:
  read disk, recover state, process one event, and emit one next action.
- Store workflow checkpoints in `plans/$FEATURE/STATE.json` and append events
  to `plans/$FEATURE/EVENTS.jsonl` using `orchestrator/eventlog.py`.
  In `strict` rigor, these files are required before any agent spawns.
- Rigor controls process depth:
  - `lite`: 4 plan files, fewer gates, review/test can be final-only when risk is low.
  - `standard`: current 8-file pipeline with review after every conversation.
  - `strict`: 8 files plus mandatory `STATE.json`, `EVENTS.jsonl`, human approvals, review, and test gates.
- Default: pause at every stage transition, require human acknowledgement.
- Auto mode: skip pauses, run to completion.
- In `standard` and `strict`, reviewer runs after every implemented conversation.
- In `lite`, reviewer may run final-only unless feedback, touched files, or user preference requires earlier review.
- After every agent completes, check for feedback files before advancing.
- Max 2 feedback cycles per conversation and feedback file. If exceeded, stop and report.
- If a stage fails, report the failure and manual recovery command. Do not retry.
- Canonical FSM reference: `docs/ORCHESTRATOR_FSM.md`.

## FSM checkpoint protocol

The orchestrator (LLM) must consult `orchestrator/` at three specific points.

### 1. Startup recovery

When `/team-flow` starts or resumes, recover state in this order:

1. **Read STATE.json** — load `plans/<feature>/STATE.json` using `State` (`orchestrator/state.py`). If the file exists and parses cleanly, use that state.
2. **Fall back to EVENTS.jsonl replay** — if STATE.json is absent or unreadable, instantiate `EventLog(feature=FEATURE)` (`orchestrator/eventlog.py`) and call `log.reconstruct_state()` (which calls `reconstruct()` from `orchestrator/reducer.py` internally). Use the resulting state.
3. **Fall back to IDLE** — if neither file exists, start from `State()` (default IDLE). In `lite` and `standard` rigor this is not an error. In `strict` rigor: stop and report "STATE.json and EVENTS.jsonl not found — cannot recover state in strict mode."

**Disk feedback wins:** After loading state, scan `plans/<feature>/feedback/` for open feedback files. If any exist and STATE.json says the pipeline is not blocked, correct the in-memory state by calling `reduce(state, FileCreatedEvent(file=highest_priority_file))` and updating logs. Disk always wins over cached STATE.json.

**Log the outcome:** Print one of:
- `[FSM] State recovered from STATE.json: <state_name>`
- `[FSM] State reconstructed from EVENTS.jsonl: <state_name> (N events)`
- `[FSM] No prior state found — starting from IDLE`
- `[FSM] State corrected by disk feedback: <old_state> → <new_state>`

### 2. Before each agent spawn

Before spawning any subagent, execute this sequence:

1. **Choose the correct event** for the transition (e.g. `CommandEvent`, `AgentDoneEvent`, `FileCreatedEvent` — all from `orchestrator/events.py`).
2. **Compute new state** — call `reduce(state, event)` from `orchestrator/reducer.py`. This is a pure function; it never has side effects.
3. **Persist the transition** — call `log.append(event)` and `log.write_state_json(new_state)` on the `EventLog` instance (`orchestrator/eventlog.py`). Both must succeed before spawning.
4. **Spawn** the subagent.

Always update `new_state` after the call so subsequent decisions use the current state.

### 3. Backward compatibility

- If `plans/<feature>/` does not exist yet, create the directory before writing STATE.json or EVENTS.jsonl.
- If any IO operation fails (disk full, permission error, etc.), log a warning — `[FSM WARNING] Could not persist state: <error>` — and proceed with the spawn. Do not block the pipeline on logging failures.
- Missing STATE.json or EVENTS.jsonl is **not an error** in `lite` or `standard` rigor. Only `strict` rigor requires these files before any agent spawn.

## FSM guards

Run these three guards in order before any forward advance in the pipeline. All three must pass before spawning the next agent or moving to the next stage.

### Guard 1 — Feedback-open check

1. Scan `plans/<feature>/feedback/` for open files.
2. If any feedback files exist:
   - Identify the highest-priority file using the priority order: `HUMAN_QUESTIONS.md`, `ARCH_FEEDBACK.md`, `DESIGN_QUESTIONS.md`, `IMPL_QUESTIONS.md`, `REVIEW_FAILURES.md`, `TEST_FAILURES.md`.
   - Call `reduce(state, FileCreatedEvent(file=highest_priority_file))` (from `orchestrator/events.py` and `orchestrator/reducer.py`), then update logs with `log.append(event)` and `log.write_state_json(new_state)`.
   - Route to the responsible agent per the priority order already defined in the "Feedback file locations" section.
3. When that agent resolves and deletes the file:
   - Call `reduce(state, FileDeletedEvent(file))` (from `orchestrator/events.py`), update logs.
   - Re-scan `plans/<feature>/feedback/` for remaining open files.
4. Only advance (proceed to Guard 2) when no feedback files remain.

### Guard 2 — Retry-count check

Run this check before routing any feedback file to its responsible agent (after Guard 1 identifies the file):

1. Check `state.retry_count_by_key["conv-N:FILE.md"]` (from `orchestrator/state.py`), where `N` is the current conversation number and `FILE.md` is the feedback filename.
2. If the value is `> 2`:
   - Do not spawn the fix agent.
   - Write `plans/<feature>/feedback/HUMAN_QUESTIONS.md` with an escalation message identifying the conversation, the file, and the retry count.
   - Call `reduce(state, FileCreatedEvent("HUMAN_QUESTIONS.md"))`, update logs.
   - Stop and report: `"Retry limit exceeded for conv-N:FILE.md. Escalated to HUMAN_QUESTIONS.md."`
3. If the value is ≤ 2:
   - After routing the fix agent (spawning it), call `reduce(state, SystemEvent(action="RETRY", retry_key="conv-N:FILE.md"))` (from `orchestrator/events.py`), update logs so the retry counter increments.

**Exception:** `IMPL_QUESTIONS.md` and `DESIGN_QUESTIONS.md` are exempt — they are clarification requests, not fix loops. Do not check or increment `retry_count_by_key` for these two files.

### Guard 3 — Zero-diff stall check

Applies only after the builder finishes a `REVIEW_FAILURES.md` fix, before re-spawning the reviewer:

1. Run:
   ```bash
   git diff HEAD -- . ":(exclude)plans/"
   ```
2. If the command fails (not a git repo or git is unavailable): skip this check, log `[FSM WARNING] git diff failed — skipping zero-diff check`, and proceed to re-spawn reviewer.
3. If the output is empty (builder made no implementation changes):
   - Call `reduce(state, NoDiffDetectedEvent())` (from `orchestrator/events.py`), update logs.
   - Write `plans/<feature>/feedback/HUMAN_QUESTIONS.md` with a `[STALL]` tag:
     ```
     [STALL] Conversation N — builder and reviewer in zero-diff loop.
     Builder claimed to fix REVIEW_FAILURES.md but no code changed.
     Human decision required: accept as-is, override the rule, or rewrite the conversation scope.
     ```
   - Stop and report: `"Zero-diff loop detected for Conv N. Escalated to HUMAN_QUESTIONS.md."`
4. If the output is non-empty: proceed to re-spawn reviewer.

## Health checks before skipping stages

Run these before jumping to the entry stage. Fail fast with a clear error.

**plan:**
- No pre-requisite check needed. Feature name is enough.
- Print: `[SKIPPED] Stage 0 (discovery) → entering at plan`

**build:**
- Check `plans/$FEATURE/` exists. If not: stop → `plans/$FEATURE/ not found. Run /team-flow $FEATURE first to create the plan.`
- If `rigor = lite`, check the 4 required plan files exist: USER_STORIES.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, CONVERSATION_PROMPTS.md.
- If `rigor = standard` or `strict`, check all 8 plan files exist: USER_STORIES.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, CONVERSATION_PROMPTS.md, HAPPY_FLOW.md, EDGE_CASES.md, ARCHITECTURE_PROPOSAL.md, FLOW_DIAGRAM.md. If any missing: stop → list the missing files.
- If `rigor = strict`, also require STATE.json and EVENTS.jsonl.
- Read PROGRESS.md — resume from last TODO conversation (do not clear or restart).
- Print: `[SKIPPED] Discovery + plan → entering at build`
- Print: `Resuming from: Conversation N (last TODO in PROGRESS.md)`

**test:**
- Check `plans/$FEATURE/` exists with required files for the selected rigor (same as build).
- Check PROGRESS.md — all conversations must be DONE. If any TODO: stop → `Not all conversations are complete. Run /team-flow $FEATURE build first.`
- Print: `[SKIPPED] Discovery + plan + implementation → entering at test`

## Feedback file locations

All feedback files live in `plans/[feature]/feedback/`.
A file existing = issue open. A file absent or deleted = resolved.

| File | Written by | Resolved by |
|---|---|---|
| `ARCH_FEEDBACK.md` | reviewer | architect |
| `REVIEW_FAILURES.md` | reviewer | builder |
| `TEST_FAILURES.md` | tester | builder |
| `IMPL_QUESTIONS.md` | builder `[REQ]` | planner (what should this do?) |
| `DESIGN_QUESTIONS.md` | builder `[ARCH]` | architect (how is this technically possible?) |
| `HUMAN_QUESTIONS.md` | any agent | user — pipeline enters `BLOCKED_ON_HUMAN` |

If multiple feedback files exist, route one at a time in this priority order:
`HUMAN_QUESTIONS.md`, `ARCH_FEEDBACK.md`, `DESIGN_QUESTIONS.md`,
`IMPL_QUESTIONS.md`, `REVIEW_FAILURES.md`, `TEST_FAILURES.md`.

## Subagent map

| Action | Spawn | Why |
|---|---|---|
| Storm | `architect` | technical exploration, opus |
| Plan | `planner` | user stories + decomposition |
| Implement | `builder` | code execution, scoped to one conversation |
| Review | `reviewer` | adversarial check after each conversation |
| Fix arch issue | `architect` | redesign before builder can continue |
| Fix impl issue | `builder` | targeted fix of review violations |
| Clarify requirement | `planner` | unblock builder on ambiguous spec |
| Test | `tester` | verify acceptance criteria |
| Fix test failure | `builder` | address failing criteria |
| Retro | `quick` | fast retrospective |

---

## Stage 0 — Discovery Path
*(skip if entryStage = plan, build, or test)*

If skipping: print the health check output from above and jump to the correct stage.

If running: print exactly this and wait for user input:

```
═══════════════════════════════════════════
  [feature-name] — Choose discovery path
═══════════════════════════════════════════

  [1] Quick storm
      Architect explores the idea now (~10 min)
      Best for: rough idea that needs shaping,
                technical unknowns to surface

  [2] Skip discovery
      Go straight to planning
      Best for: you already know what to build,
                small or familiar feature

  [3] Import PRD
      You have a requirements file ready
      Best for: BMAD output, hand-written PRD,
                any structured requirements doc

Reply with 1, 2, or 3:
```

**On '1'** → proceed to Stage 1 (Storm), then Stage 2 (Plan)

**On '2'** → skip Stage 1, go straight to Stage 2 (Plan)
  - Print: `Skipping discovery. Starting planning...`

**On '3'** → ask:
  ```
  Path to your PRD file? (e.g. docs/feature-prd.md)
  ```
  Wait for path input. Then:
  - Run `/prd-import [feature] [path] [rigor]`
  - Print: `PRD imported. Plan files ready in plans/[feature]/`
  - Skip Stage 1 and Stage 2 entirely (prd-import already generated the selected rigor's plan files)
  - Jump directly to Stage 3 (Implement)

---

## Stage 1 — Storm
*(only runs if user chose path 1)*

**Spawn** `architect`:
```
Run /storm for the feature: [feature name]
Explore the idea technically — layers, dependencies, design decisions.
When the user is satisfied, they will type /stop plan to write STORM_SEED.md.
Remind them of this at the start.
```

If not autoFlow — **PAUSE:**
```
[Stage 1 — Storm complete]
STORM_SEED.md written (or skipped).
Ready to plan? Reply 'yes' to continue, or 'no' to stop here.
```
After user replies:
- If reply is a proceed signal ('yes', 'go', 'continue', 'done', or a numeric choice): call `reduce(state, HumanResponseEvent(value=reply))` (from `orchestrator/events.py` and `orchestrator/reducer.py`), update logs with `log.append(event)` and `log.write_state_json(new_state)`, then advance.
- If reply is a stop signal ('no', 'stop'): call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, write `STATE.json` via `log.write_state_json(new_state)`, then halt.
- If reply is unrecognised: re-prompt without recording a `HUMAN_RESPONSE` event.

If autoFlow: record `HumanResponseEvent(value="auto-advance")` at this skipped pause, update logs.

On 'no': stop.

---

## Stage 2 — Plan
*(only runs if user chose path 1 or 2)*

**Spawn** `planner`:
```
Run /plan [feature name] [rigor].
If plans/STORM_SEED.md exists, consume it as pre-filled answers.
Ensure every story references which phase/conversation delivers it.
Ensure every phase references which stories it fulfills.
After creating the selected rigor's plan files, list them as a summary.
```

If not autoFlow — **PAUSE:**
```
[Stage 2 — Plan complete]
plans/[feature]/ created with the selected rigor's required files.
Review USER_STORIES.md and CONVERSATION_PROMPTS.md.
Reply 'go' to start implementation, or 'stop' to pause here.
```
After user replies:
- If reply is a proceed signal ('yes', 'go', 'continue', 'done', or a numeric choice): call `reduce(state, HumanResponseEvent(value=reply))`, update logs, then advance.
- If reply is a stop signal ('no', 'stop'): call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, write `STATE.json` via `log.write_state_json(new_state)`, then halt.
- If reply is unrecognised: re-prompt without recording a `HUMAN_RESPONSE` event.

If autoFlow: record `HumanResponseEvent(value="auto-advance")` at this skipped pause, update logs.

On 'stop': exit.

---

## Stage 3 — Implement + Review Loop

Read `plans/[feature]/PROGRESS.md`.
Track `retryCount = 0` per conversation.

While any conversation row has status TODO:

  **3a. Builder implements**

  **Spawn** `builder`:
  ```
  Run /build [feature] in manual mode.
  Execute conversation N only. Verify, update PROGRESS.md.
  If you hit requirement ambiguity (what should this do?): write plans/[feature]/feedback/IMPL_QUESTIONS.md
  If you hit a technical blocker (how is this possible?): write plans/[feature]/feedback/DESIGN_QUESTIONS.md
  Use formats from ~/.claude/FEEDBACK_PROTOCOL.md, then report blocked.
  Report: files changed, verify result, stories delivered.
  ```

  After builder completes — check for feedback files:

  → If `IMPL_QUESTIONS.md` exists (contains [REQ] tagged questions):
    **Spawn** `planner`:
    ```
    Read plans/[feature]/feedback/IMPL_QUESTIONS.md.
    Answer each [REQ] question — clarify in USER_STORIES.md or CONVERSATION_PROMPTS.md.
    Delete plans/[feature]/feedback/IMPL_QUESTIONS.md when resolved.
    ```

  → If `DESIGN_QUESTIONS.md` exists (contains [ARCH] tagged questions):
    **Spawn** `architect`:
    ```
    Read plans/[feature]/feedback/DESIGN_QUESTIONS.md.
    Resolve each [ARCH] question — update ARCHITECTURE_PROPOSAL.md with the approach, or IMPLEMENTATION_PLAN.md if this is a lite plan without ARCHITECTURE_PROPOSAL.md.
    Delete plans/[feature]/feedback/DESIGN_QUESTIONS.md when resolved.
    ```

  Both files can exist at the same time. Route one agent at a time using the FSM priority order.
  After both resolve → builder re-implements (do not increment retryCount for these).

  **3b. Reviewer checks**

  If `rigor = lite`, reviewer may run once after the final builder conversation unless feedback files, risky touched files, or user preference require per-conversation review.

  If `rigor = standard` or `strict`, reviewer runs after every builder conversation.

  If review is required for this point in the selected rigor, **spawn** `reviewer`:
  ```
  Review the changes from conversation N of [feature].
  Run: git diff HEAD~1 HEAD (or git diff --staged if not yet committed).
  Check against plans/[feature]/ARCHITECTURE_PROPOSAL.md and any rules in .claude/rules/ if present.
  If architectural violations found: write plans/[feature]/feedback/ARCH_FEEDBACK.md
  If implementation violations found: write plans/[feature]/feedback/REVIEW_FAILURES.md
  Use formats from ~/.claude/FEEDBACK_PROTOCOL.md.
  If all clear: report PASS.
  ```

  If lite skips review for this conversation, continue to **3c. Advance** after checking feedback files.

  After reviewer completes — check feedback files:

  → If `ARCH_FEEDBACK.md` exists:
    Increment retryCount. If retryCount > 2: STOP — report "Feedback loop exceeded for Conv N. Manual intervention required."

    **Spawn** `architect`:
    ```
    Read plans/[feature]/feedback/ARCH_FEEDBACK.md.
    Redesign the affected architecture in plans/[feature]/ARCHITECTURE_PROPOSAL.md, or plans/[feature]/IMPLEMENTATION_PLAN.md for lite plans without ARCHITECTURE_PROPOSAL.md.
    If phases need to change, update plans/[feature]/IMPLEMENTATION_PLAN.md.
    Delete plans/[feature]/feedback/ARCH_FEEDBACK.md when resolved.
    Report: what changed in the design.
    ```
    After architect resolves → go back to 3a (builder re-implements Conv N).

  → If `REVIEW_FAILURES.md` exists:
    Increment retryCount. If retryCount > 2: STOP — report "Feedback loop exceeded for Conv N. Manual intervention required."

    **Spawn** `builder`:
    ```
    Read plans/[feature]/feedback/REVIEW_FAILURES.md.
    Fix each violation listed. Do not change anything outside the listed violations.
    Delete plans/[feature]/feedback/REVIEW_FAILURES.md when all fixed.
    ```

    After builder completes — **zero-diff check** before re-spawning reviewer:
    ```bash
    git diff HEAD -- . ":(exclude)plans/" 2>/dev/null
    ```
    If the diff is empty (builder made no implementation changes):
    - Write `plans/[feature]/feedback/HUMAN_QUESTIONS.md`:
      ```
      [STALL] Conversation N — builder and reviewer in zero-diff loop.
      Builder claimed to fix REVIEW_FAILURES.md but no code changed.
      Violations: [paste REVIEW_FAILURES.md content]
      Human decision required: accept as-is, override the rule, or rewrite the conversation scope.
      ```
    - STOP. Report: "Zero-diff loop detected for Conv N. Escalated to HUMAN_QUESTIONS.md — manual intervention required."

    If diff is non-empty → go back to 3b (reviewer re-checks).

  → If no feedback files: reviewer passed.

  **3c. Advance**

  If not autoFlow — **PAUSE:**
  ```
  [Stage 3 — Conversation N complete + reviewed]
  Reviewer: PASS. Commit your changes now.
  Reply 'continue' for the next conversation, or 'stop' to pause here.
  ```
  After user replies:
  - If reply is a proceed signal ('yes', 'go', 'continue', 'done', or a numeric choice): call `reduce(state, HumanResponseEvent(value=reply))`, update logs, then advance.
  - If reply is a stop signal ('no', 'stop'): call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, write `STATE.json` via `log.write_state_json(new_state)`, then halt.
  - If reply is unrecognised: re-prompt without recording a `HUMAN_RESPONSE` event.

  If autoFlow: record `HumanResponseEvent(value="auto-advance")` at this skipped pause, update logs.

  On 'stop': exit.

  Reset retryCount = 0. Proceed to next TODO conversation.

---

## Stage 4 — Test + Fix Loop

**Pre-gate — all conversations must be DONE:**

1. Read `plans/<feature>/PROGRESS.md` and check every conversation row in the "Conversation Breakdown" table.
2. If any row has status other than `DONE`: stop and report:
   ```
   Not all conversations are complete. Run /team-flow <feature> build first. Incomplete: Conv N
   ```
   (Replace `N` with the number(s) of the incomplete conversation(s).)
3. When all conversation rows are `DONE`:
   - Call `reduce(state, ImplementCompleteEvent())` (from `orchestrator/events.py` and `orchestrator/reducer.py`). The resulting state must be `TESTING`.
   - Update logs: call `log.append(event)` and `log.write_state_json(new_state)` on the `EventLog` instance (`orchestrator/eventlog.py`).
   - Then proceed to spawn tester below.

Track `testRetryCount = 0`.

**Spawn** `tester`:
```
Read plans/[feature]/USER_STORIES.md.
Run /test to verify each acceptance criterion.
For each criterion: PASS / FAIL / NOT COVERED.
If any FAIL or NOT COVERED: write plans/[feature]/feedback/TEST_FAILURES.md
using the format in ~/.claude/FEEDBACK_PROTOCOL.md.
```

In `lite`, testing may be limited to the verify commands and directly relevant checks from the plan.

In `standard`, tester verifies acceptance criteria before retro.

In `strict`, tester must map every acceptance criterion to PASS / FAIL / NOT COVERED and cannot proceed with NOT COVERED criteria.

After tester completes — check for `TEST_FAILURES.md`:

→ If `TEST_FAILURES.md` exists:
  Increment testRetryCount. If testRetryCount > 2: STOP — report "Test failures unresolved after 2 fix cycles. Manual intervention required."

  **Spawn** `builder`:
  ```
  Read plans/[feature]/feedback/TEST_FAILURES.md.
  Fix each failing or uncovered criterion.
  Delete plans/[feature]/feedback/TEST_FAILURES.md when resolved.
  ```
  After builder resolves → re-spawn tester (go back to start of Stage 4).

→ If no TEST_FAILURES.md: all criteria pass.

If not autoFlow — **PAUSE:**
```
[Stage 4 — Test complete]
All acceptance criteria: PASS.
Reply 'done' to proceed to retro.
```
After user replies:
- If reply is a proceed signal ('yes', 'go', 'continue', 'done', or a numeric choice): call `reduce(state, HumanResponseEvent(value=reply))`, update logs, then advance.
- If reply is a stop signal ('no', 'stop'): call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, write `STATE.json` via `log.write_state_json(new_state)`, then halt.
- If reply is unrecognised: re-prompt without recording a `HUMAN_RESPONSE` event.

If autoFlow: record `HumanResponseEvent(value="auto-advance")` at this skipped pause, update logs.

---

## Stage 5 — Retro

**Spawn** `quick`:
```
Run /retro [feature].
Ask the 3 retrospective questions and write RETRO.md.
```

Report:
```
[Stage 5 — Retro complete]
Pipeline complete. RETRO.md written to plans/[feature]/.
Lessons appended to LESSONS_CANDIDATE.md (if any were extracted).
Feature '[feature]' is DONE.

To promote lessons to active memory: /lessons
```
