---
name: help
description: Detect current project state and show numbered options the user can pick. Activates the chosen action immediately. Pass a feature name to get state for that feature.
argument-hint: "[feature-name]"
model: haiku
---

## Pathly Command Surface

Use `/pathly <command>` as the canonical cross-framework command form. `/path <command>` is the short alias. Legacy direct skill commands may remain available in some hosts for backwards compatibility, but user-facing guidance should prefer `/pathly` or `/path`.

## Doctor mode (`/pathly doctor`)

If `$ARGUMENTS` contains `--doctor` (e.g. `/pathly doctor` or `/pathly help my-feature --doctor`),
run the diagnostic flow below instead of the normal menu. Extract the feature name from
`$ARGUMENTS` if one is provided alongside `--doctor`; otherwise scan `plans/` for the most
recently modified feature folder.

### Doctor Step 1 — Run verify-state internally

Perform every check from the `verify-state` skill (Checks A through D) for the target feature.
Collect all flagged issues.

### Doctor Step 2 — Check additional stuck-state indicators

Beyond what verify-state checks, also look for:

- **STATE.json says BUILDING but no conversations are in_progress in PROGRESS.md** →
  FSM stuck: builder may have exited mid-run.
- **Feedback file has expired TTL** (from frontmatter `created_at + ttl_hours`) →
  stale orphan from a previous run.
- **Feedback file event ID not in EVENTS.jsonl** → orphan from a different session.
- **REVIEW_FAILURES.md exists but git diff shows no changes since it was written** →
  builder loop (zero-diff stall).

### Doctor Step 3 — Report in plain language

Print a diagnostic summary in this format:

```
╔══════════════════════════════════════════╗
  /pathly doctor — <feature>
╚══════════════════════════════════════════╝

✓  Everything looks healthy.
```

Or, if issues found:

```
╔══════════════════════════════════════════╗
  /pathly doctor — <feature>
  N issue(s) found
╚══════════════════════════════════════════╝

Issue 1: REVIEW_FAILURES.md is a leftover from a previous run
  Why: its event ID (2026-04-28T10:00:00Z) does not appear in the current EVENTS.jsonl.
  Suggestion: delete plans/<feature>/feedback/REVIEW_FAILURES.md

Issue 2: STATE.json says BUILDING but no conversation is active
  Why: PROGRESS.md shows all conversations as either DONE or TODO — none are in_progress.
  Suggestion: run /pathly flow <feature> build to return the pipeline to a stable state.

────────────────────────────────────────────
Run suggestion 1? [yes / no / show all suggestions]
```

### Doctor Step 4 — Offer action

If there are suggestions, ask: `Run suggestion 1? [yes / no / show all suggestions]`

- **yes** → execute the first suggestion (delete orphan file, or run the recommended command)
- **no** → print the full list of suggestions and stop
- **show all suggestions** → print the full list and ask "Which suggestion to run? [1/2/…/none]"

**Rules for doctor mode:**
- Never auto-fix without explicit user confirmation.
- If a suggestion is "delete a file", show the file path clearly before confirming.
- If a suggestion is "run a command", show the exact command before running.
- One action at a time — do not batch multiple fixes without explicit approval.

---

## Step 1: Detect state

Check in this order:

1. If `$ARGUMENTS` is provided, use it as `FEATURE`.
   Otherwise scan `plans/` for the most recently modified feature folder.

2. Read `plans/$FEATURE/PROGRESS.md` if it exists.

3. Check `plans/$FEATURE/feedback/` for open files.

4. Infer current rigor:
   - **lite** — required 4 files exist, but one or more standard files are missing:
     `HAPPY_FLOW.md`, `EDGE_CASES.md`, `ARCHITECTURE_PROPOSAL.md`, `FLOW_DIAGRAM.md`
   - **standard** — all 8 plan files exist, but strict audit files or strict markers are missing
   - **strict** — all 8 plan files exist and `STATE.json` + `EVENTS.jsonl` exist, or the plan explicitly says `Rigor: strict`
   - **unknown** — no plan folder exists yet

5. Print the inferred rigor in every feature-specific menu banner:
   `Rigor: lite|standard|strict|unknown`

6. Classify into one of these states:
   - **no-feature** — no plans/ folder or no feature found
   - **storm-done** — `plans/STORM_SEED.md` exists, no plans folder yet
   - **plan-done** — plans folder exists, at least one conversation TODO, no open feedback
   - **feedback-open** — plans folder exists, feedback file(s) present
   - **build-done** — all conversations DONE, no RETRO.md yet
   - **retro-done** — RETRO.md exists

---

## Step 2: Print interactive menu

Print the banner, then the numbered options for the detected state. Wait for user input.

### State: no-feature

```
═══════════════════════════════════════════
  Claude Agents Framework
  No active feature found
═══════════════════════════════════════════

  What do you want to do?

  [1] Describe what you want (plain English)  → /pathly
  [2] Start a new feature (full pipeline)     → /pathly flow
  [3] Start a new feature with a PRD/BMAD file
  [4] See all commands

Reply with 1, 2, 3, or 4:
```

On '1': ask "What do you want to build?" → run `/pathly <answer>`
On '2': ask "Feature name?" → run `/pathly flow <name>`
On '3': ask "Feature name?" then "PRD or BMAD file path?" → run `/pathly flow <name>` and user selects [3] at the path selector
On '4': print full command reference (Step 3)

---

### State: storm-done

```
═══════════════════════════════════════════
  Storm complete — STORM_SEED.md ready
═══════════════════════════════════════════

  What do you want to do?

  [1] Plan the feature now      → /pathly plan <feature>
  [2] Run full pipeline         → /pathly flow <feature>
  [3] See all commands

Reply with 1, 2, or 3:
```

On '1': run `/pathly plan <feature>`
On '2': run `/pathly flow <feature>`
On '3': print full command reference

---

### State: plan-done

Read PROGRESS.md: X conversations done, Y remaining.

```
═══════════════════════════════════════════
  <feature> — Plan ready
  Conv: X done · Y remaining
  Rigor: lite|standard|strict
═══════════════════════════════════════════

  What do you want to do?

  [1] Continue building         → next TODO conversation
  [2] Run full pipeline         → build + review + test + retro
  [3] Run full pipeline (fast)  → no pause points
  [4] Review current code       → /pathly review
  [5] Change rigor              → see options
  [6] See all commands

Reply with 1–6:
```

On '1': run `/pathly flow <feature> build`
On '2': run `/pathly flow <feature> build`  (with pauses)
On '3': run `/pathly flow <feature> build fast`
On '4': run `/pathly review`
On '5': print the "CHANGING RIGOR" section from Step 3
On '6': print full command reference

---

### State: feedback-open

List which feedback files exist and who must act.

```
═══════════════════════════════════════════
  <feature> — Open feedback requires action
  Rigor: lite|standard|strict
═══════════════════════════════════════════

  Open files:
    REVIEW_FAILURES.md → builder must fix
    [other files if present]

  What do you want to do?

  [1] Resume pipeline (routes to correct agent automatically)
  [2] See the feedback file contents
  [3] See all commands

Reply with 1, 2, or 3:
```

On '1': run `/pathly flow <feature> build`
On '2': read and print the feedback file(s)
On '3': print full command reference

---

### State: build-done

```
═══════════════════════════════════════════
  <feature> — All conversations complete
  Rigor: lite|standard|strict
═══════════════════════════════════════════

  What do you want to do?

  [1] Run tests                 → tester verifies all ACs
  [2] Run tests + retro         → full finish
  [3] Write retro only          → /pathly retro <feature>
  [4] See all commands

Reply with 1–4:
```

On '1': run `/pathly flow <feature> test`
On '2': run `/pathly flow <feature> test` (includes retro at end)
On '3': run `/pathly retro <feature>`
On '4': print full command reference

---

### State: retro-done

```
═══════════════════════════════════════════
  <feature> — DONE ✓
  RETRO.md written
  Rigor: lite|standard|strict
═══════════════════════════════════════════

  What do you want to do?

  [1] Archive this feature      → moves to plans/.archive/
  [2] Promote lessons           → /pathly lessons (update active memory)
  [3] Start next feature        → /pathly flow <new-feature>
  [4] Read the retro            → show RETRO.md
  [5] See all commands

Reply with 1–5:
```

On '1': run `/pathly archive <feature>`
On '2': run `/pathly lessons`
On '3': ask "New feature name?" → run `/pathly flow <name>`
On '4': read and print RETRO.md
On '5': print full command reference

---

## Step 3: Full command reference (shown on request only)

```
───────────────────────────────────────────
  ENTRY POINTS
───────────────────────────────────────────

  /pathly                                prompts "What do you want?" → routes
  /pathly <what you want>                skip prompt, routes immediately
  /pathly help [feature]                    detect state → show this menu
  /pathly doctor [feature]           diagnose stuck FSM, orphan files, stale feedback

───────────────────────────────────────────
  MAIN COMMAND
───────────────────────────────────────────

  /pathly flow <feature>               full pipeline, standard rigor by default
  /pathly flow <feature> lite          small change, 4-file plan, lighter gates
  /pathly flow <feature> standard      current full 8-file pipeline
  /pathly flow <feature> strict        mandatory approvals + audit-grade gates
  /pathly flow <feature> build         skip to build stage
  /pathly flow <feature> test          skip to test stage
  /pathly flow <feature> plan          skip discovery, start planning
  /pathly flow <feature> fast          no pause points
  /pathly flow <feature> build fast    resume build, no pauses

───────────────────────────────────────────
  INDIVIDUAL STAGES
───────────────────────────────────────────

  /pathly storm                             architect explores idea → STORM_SEED.md
  /pathly plan <feature> [rigor]            planner creates 4 or 8 plan files
  /pathly continue <feature>                   builder implements next TODO conversation
  /pathly review                            reviewer audits staged changes
  /pathly retro <feature>                   quick summarizes; retro skill writes RETRO.md + extracts lessons
  /pathly lessons                           promote candidate lessons → LESSONS.md
  /pathly archive <feature>                 move completed feature to plans/.archive/
  /pathly prd-import <feature> <file> [rigor] translate any PRD file → plan files
  /pathly bmad-import <feature> <file> [rigor] translate BMAD PRD → plan files
  /pathly verify-state [feature]            check stale feedback, PROGRESS drift, dead references

───────────────────────────────────────────
  CHANGING RIGOR
───────────────────────────────────────────

  /pathly help [feature] should show the inferred current rigor.

  Upgrade lite → standard:
    /pathly plan <feature> standard
    Adds missing standard files. Keeps existing plan content.

  Upgrade standard → strict:
    /pathly plan <feature> strict
    Adds strict risk, rollback, approval, and verification mapping.

  Downgrade strict → standard:
    /pathly flow <feature> standard
    Uses standard gates from now on. Do not delete audit files.

  Downgrade standard → lite:
    /pathly flow <feature> lite
    Uses lighter gates from now on. Keep extra plan files as references.

  Never delete plan files just to downgrade. Rigor controls future gates.

───────────────────────────────────────────
  FEEDBACK FILES  (plans/<feature>/feedback/)
───────────────────────────────────────────

  ARCH_FEEDBACK.md     reviewer → architect   (BLOCKING)
  REVIEW_FAILURES.md   reviewer → builder
  IMPL_QUESTIONS.md    builder [REQ]  → planner
  DESIGN_QUESTIONS.md  builder [ARCH] → architect
  TEST_FAILURES.md     tester   → builder
  HUMAN_QUESTIONS.md   any agent → user (BLOCKED_ON_HUMAN)

  File present = issue open. Deleted = resolved.

───────────────────────────────────────────
  DOCS
───────────────────────────────────────────

  docs/ARCHITECTURE_AGENTS.md   full pipeline + agent map
  docs/ORCHESTRATOR_FSM.md      deterministic workflow state machine
  docs/FEEDBACK_PROTOCOL.md     feedback file formats
  docs/CONCEPTS.md              philosophy
  https://github.com/hamilton-sky/claude-agents-framework

═══════════════════════════════════════════
```
