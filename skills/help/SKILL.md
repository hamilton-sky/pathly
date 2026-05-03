---
name: help
description: Detect current project state and show numbered options the user can pick. Activates the chosen action immediately. Pass a feature name to get state for that feature.
argument-hint: "[feature-name]"
model: haiku
---

## Step 1: Detect state

Check in this order:

1. If `$ARGUMENTS` is provided, use it as `FEATURE`.
   Otherwise scan `plans/` for the most recently modified feature folder.

2. Read `plans/$FEATURE/PROGRESS.md` if it exists.

3. Check `plans/$FEATURE/feedback/` for open files.

4. Classify into one of these states:
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

  [1] Describe what you want (plain English)  → /go
  [2] Start a new feature (full pipeline)     → /team-flow
  [3] Start a new feature with a PRD file
  [4] See all commands

Reply with 1, 2, 3, or 4:
```

On '1': ask "What do you want to build?" → run `/go <answer>`
On '2': ask "Feature name?" → run `/team-flow <name>`
On '3': ask "Feature name?" then "PRD file path?" → run `/team-flow <name>` and user selects [3] at the path selector
On '4': print full command reference (Step 3)

---

### State: storm-done

```
═══════════════════════════════════════════
  Storm complete — STORM_SEED.md ready
═══════════════════════════════════════════

  What do you want to do?

  [1] Plan the feature now      → /plan <feature>
  [2] Run full pipeline         → /team-flow <feature>
  [3] See all commands

Reply with 1, 2, or 3:
```

On '1': run `/plan <feature>`
On '2': run `/team-flow <feature>`
On '3': print full command reference

---

### State: plan-done

Read PROGRESS.md: X conversations done, Y remaining.

```
═══════════════════════════════════════════
  <feature> — Plan ready
  Conv: X done · Y remaining
═══════════════════════════════════════════

  What do you want to do?

  [1] Continue building         → next TODO conversation
  [2] Run full pipeline         → build + review + test + retro
  [3] Run full pipeline (fast)  → no pause points
  [4] Review current code       → /review
  [5] See all commands

Reply with 1–5:
```

On '1': run `/team-flow <feature> build`
On '2': run `/team-flow <feature> build`  (with pauses)
On '3': run `/team-flow <feature> build fast`
On '4': run `/review`
On '5': print full command reference

---

### State: feedback-open

List which feedback files exist and who must act.

```
═══════════════════════════════════════════
  <feature> — Open feedback requires action
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

On '1': run `/team-flow <feature> build`
On '2': read and print the feedback file(s)
On '3': print full command reference

---

### State: build-done

```
═══════════════════════════════════════════
  <feature> — All conversations complete
═══════════════════════════════════════════

  What do you want to do?

  [1] Run tests                 → tester verifies all ACs
  [2] Run tests + retro         → full finish
  [3] Write retro only          → /retro <feature>
  [4] See all commands

Reply with 1–4:
```

On '1': run `/team-flow <feature> test`
On '2': run `/team-flow <feature> test` (includes retro at end)
On '3': run `/retro <feature>`
On '4': print full command reference

---

### State: retro-done

```
═══════════════════════════════════════════
  <feature> — DONE ✓
  RETRO.md written
═══════════════════════════════════════════

  What do you want to do?

  [1] Archive this feature      → moves to plans/.archive/
  [2] Promote lessons           → /lessons (update active memory)
  [3] Start next feature        → /team-flow <new-feature>
  [4] Read the retro            → show RETRO.md
  [5] See all commands

Reply with 1–5:
```

On '1': run `/archive <feature>`
On '2': run `/lessons`
On '3': ask "New feature name?" → run `/team-flow <name>`
On '4': read and print RETRO.md
On '5': print full command reference

---

## Step 3: Full command reference (shown on request only)

```
───────────────────────────────────────────
  ENTRY POINTS
───────────────────────────────────────────

  /go                                prompts "What do you want?" → routes
  /go <what you want>                skip prompt, routes immediately
  /help [feature]                    detect state → show this menu

───────────────────────────────────────────
  MAIN COMMAND
───────────────────────────────────────────

  /team-flow <feature>               full pipeline, path selector at start
  /team-flow <feature> build         skip to build stage
  /team-flow <feature> test          skip to test stage
  /team-flow <feature> plan          skip discovery, start planning
  /team-flow <feature> fast          no pause points
  /team-flow <feature> build fast    resume build, no pauses

───────────────────────────────────────────
  INDIVIDUAL STAGES
───────────────────────────────────────────

  /storm                             architect explores idea → STORM_SEED.md
  /plan <feature>                    planner creates 8 plan files
  /build <feature>                   builder implements next TODO conversation
  /review                            reviewer audits staged changes
  /retro <feature>                   quick writes RETRO.md + extracts lessons
  /lessons                           promote candidate lessons → LESSONS.md
  /archive <feature>                 move completed feature to plans/.archive/
  /prd-import <feature> <file>       translate PRD file → 8 plan files

───────────────────────────────────────────
  FEEDBACK FILES  (plans/<feature>/feedback/)
───────────────────────────────────────────

  ARCH_FEEDBACK.md     reviewer → architect   (BLOCKING)
  REVIEW_FAILURES.md   reviewer → builder
  IMPL_QUESTIONS.md    builder  → planner
  DESIGN_QUESTIONS.md  builder  → architect
  TEST_FAILURES.md     tester   → builder

  File present = issue open. Deleted = resolved.

───────────────────────────────────────────
  DOCS
───────────────────────────────────────────

  docs/ARCHITECTURE_AGENTS.md   full pipeline + agent map
  docs/FEEDBACK_PROTOCOL.md     feedback file formats
  docs/CONCEPTS.md              philosophy
  https://github.com/hamilton-sky/claude-agents-framework

═══════════════════════════════════════════
```
