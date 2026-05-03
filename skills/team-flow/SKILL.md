---
name: team-flow
description: Full feature pipeline with feedback loops — discovery → plan → (implement → review → fix?) × N → test → (fix?) → retro. Reviewer runs after every conversation. Feedback files route issues to the right agent automatically. Add 'fast' to skip pause points. Add 'build', 'plan', or 'test' to enter mid-pipeline.
argument-hint: "<feature-name> [fast] [plan|build|test]"
---

Run the full feature pipeline for `$ARGUMENTS`.

## Argument parsing

Parse `$ARGUMENTS` for these tokens (order doesn't matter):
- First word that is not a keyword = `FEATURE` (the feature name)
- `fast` → set `autoFlow = true` (no pause points)
- `plan` → set `entryStage = plan`
- `build` → set `entryStage = build`
- `test` → set `entryStage = test`
- Default: `entryStage = discovery`

Examples:
```
/team-flow hotel-search              ← full pipeline, path selector
/team-flow hotel-search build        ← skip to build stage
/team-flow hotel-search test         ← skip to test stage
/team-flow hotel-search fast         ← full pipeline, no pauses
/team-flow hotel-search build fast   ← resume build, no pauses
```

## Core rules

- Spawn the right subagent for each stage — never execute work yourself.
- Default: pause at every stage transition, require human acknowledgement.
- Auto mode: skip pauses, run to completion.
- **Reviewer runs after every implemented conversation** — not just at the end.
- After every agent completes, check for feedback files before advancing.
- Max 2 feedback cycles per conversation. If exceeded, stop and report.
- If a stage fails, report the failure and manual recovery command. Do not retry.

## Health checks before skipping stages

Run these before jumping to the entry stage. Fail fast with a clear error.

**plan:**
- No pre-requisite check needed. Feature name is enough.
- Print: `[SKIPPED] Stage 0 (discovery) → entering at plan`

**build:**
- Check `plans/$FEATURE/` exists. If not: stop → `plans/$FEATURE/ not found. Run /team-flow $FEATURE first to create the plan.`
- Check all 8 plan files exist: USER_STORIES.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, CONVERSATION_PROMPTS.md, HAPPY_FLOW.md, EDGE_CASES.md, ARCHITECTURE_PROPOSAL.md, FLOW_DIAGRAM.md. If any missing: stop → list the missing files.
- Read PROGRESS.md — resume from last TODO conversation (do not clear or restart).
- Print: `[SKIPPED] Discovery + plan → entering at build`
- Print: `Resuming from: Conversation N (last TODO in PROGRESS.md)`

**test:**
- Check `plans/$FEATURE/` exists with all 8 files (same as build).
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
| `IMPL_QUESTIONS.md` | builder | planner (what should this do?) |
| `DESIGN_QUESTIONS.md` | builder | architect (how is this technically possible?) |

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
  - Run `/prd-import [feature] [path]`
  - Print: `PRD imported. Plan files ready in plans/[feature]/`
  - Skip Stage 1 and Stage 2 entirely (prd-import already generated all 8 plan files)
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
On 'no': stop.

---

## Stage 2 — Plan
*(only runs if user chose path 1 or 2)*

**Spawn** `planner`:
```
Run /plan [feature name].
If plans/STORM_SEED.md exists, consume it as pre-filled answers.
Ensure every story references which phase/conversation delivers it.
Ensure every phase references which stories it fulfills.
After creating the 8 plan files, list them as a summary.
```

If not autoFlow — **PAUSE:**
```
[Stage 2 — Plan complete]
plans/[feature]/ created with 8 files.
Review USER_STORIES.md and CONVERSATION_PROMPTS.md.
Reply 'go' to start implementation, or 'stop' to pause here.
```
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

  After builder completes — check for `IMPL_QUESTIONS.md`:

  → If `IMPL_QUESTIONS.md` exists:
    **Spawn** `planner`:
    ```
    Read plans/[feature]/feedback/IMPL_QUESTIONS.md.
    Clarify the requirement in USER_STORIES.md or CONVERSATION_PROMPTS.md.
    Delete plans/[feature]/feedback/IMPL_QUESTIONS.md when resolved.
    ```
    After planner resolves → builder re-implements (do not increment retryCount for this).

  **3b. Reviewer checks**

  **Spawn** `reviewer`:
  ```
  Review the changes from conversation N of [feature].
  Run /review last (or /review staged if not yet committed).
  Check against .claude/rules/ — three-layer contract, resolver injection, cfg lists.
  If architectural violations found: write plans/[feature]/feedback/ARCH_FEEDBACK.md
  If implementation violations found: write plans/[feature]/feedback/REVIEW_FAILURES.md
  Use formats from ~/.claude/FEEDBACK_PROTOCOL.md.
  If all clear: report PASS.
  ```

  After reviewer completes — check feedback files:

  → If `ARCH_FEEDBACK.md` exists:
    Increment retryCount. If retryCount > 2: STOP — report "Feedback loop exceeded for Conv N. Manual intervention required."

    **Spawn** `architect`:
    ```
    Read plans/[feature]/feedback/ARCH_FEEDBACK.md.
    Redesign the affected architecture in plans/[feature]/ARCHITECTURE_PROPOSAL.md.
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
    After builder resolves → go back to 3b (reviewer re-checks).

  → If no feedback files: reviewer passed.

  **3c. Advance**

  If not autoFlow — **PAUSE:**
  ```
  [Stage 3 — Conversation N complete + reviewed]
  Reviewer: PASS. Commit your changes now.
  Reply 'continue' for the next conversation, or 'stop' to pause here.
  ```
  On 'stop': exit.

  Reset retryCount = 0. Proceed to next TODO conversation.

---

## Stage 4 — Test + Fix Loop

Track `testRetryCount = 0`.

**Spawn** `tester`:
```
Read plans/[feature]/USER_STORIES.md.
Run /test to verify each acceptance criterion.
For each criterion: PASS / FAIL / NOT COVERED.
If any FAIL or NOT COVERED: write plans/[feature]/feedback/TEST_FAILURES.md
using the format in ~/.claude/FEEDBACK_PROTOCOL.md.
```

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
