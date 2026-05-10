# pathly

This is the canonical Pathly dispatcher. It reads `$ARGUMENTS`, extracts the
subcommand, and executes the matching behavior inline.

## Routing

Split `$ARGUMENTS` into:
- **subcommand** — first word (lowercase)
- **args** — everything after the first word

| subcommand | aliases | behavior |
|---|---|---|
| (empty) | — | → **help** |
| `start` | `s` | → **start** |
| `go` | `g`, `continue`, `resume`, `next` | → **go** |
| `end` | `done`, `finish`, `wrap` | → **end** |
| `pause` | `stop` | → **pause** |
| `help` | `h`, `?` | → **help** |
| `meet` | — | → **meet** |
| anything else | — | treat all of `$ARGUMENTS` as intent → **go** |

Before invoking, print:
```
Pathly route: <subcommand>
```

---

## Behavior: start

You are the Director entry point. Greet the user and route to the right workflow.

Print:

```
Welcome to Pathly. What do you want to do?

  (1) /pathly go        — describe what you want to build or continue
  (2) /pathly go storm  — brainstorm or shape an unclear idea
  (3) /pathly help      — show the state-aware menu

Reply with 1, 2, or 3 — or just describe what you want:
```

Wait for user input. Then route:

- **1 or go**: route to **go** behavior (ask for intent if not provided)
- **2 or storm**: ask "What idea do you want to explore?" → invoke `storm <answer>`
- **3 or help**: route to **help** behavior
- **Free text**: treat as intent and route via **go** behavior

---

## Behavior: go

You are the Director entry point for the agent pipeline. Read project state,
understand intent, choose the lightest safe workflow, invoke the right skill.

Never execute implementation work yourself. Route to the right skill and let it run.

**Step 0 — Get Intent**

Use `args` as the intent. If `args` is empty, ask:

```
What do you want to build or do?
```

Wait for reply.

**Step 1 — Read Project State**

1. Does `plans/` exist and contain feature folders?
2. For each folder in `plans/` (skip `.archive/`), read `PROGRESS.md` if present.
3. Count TODO vs DONE conversations.
4. Check `git status --short`.

**Step 2 — Classify Intent**

| Intent | Signals | Route |
|---|---|---|
| `tiny_change` | copy tweak, config, one obvious bug, "quick fix" | `team-flow <feature> nano` |
| `new_feature` | build, add, create, implement, make, I want | `team-flow <feature> <rigor>` |
| `brainstorm` | brainstorm, storm, refine, unclear idea | `storm <topic>` |
| `resume` | continue, resume, finish, next step, keep going | `team-flow <feature> build` |
| `test` | test, verify, acceptance criteria, QA | `team-flow <feature> test` |
| `fix_or_review` | fix, broken, bug, check diff, review | `review` or `team-flow <feature> nano` |
| `retro` | retro, wrap up, lessons, done building | `retro <feature>` |
| `unclear` | anything else | ask one clarifying question |

Feature name: strip filler words, kebab-case the useful phrase, match to existing
`plans/<name>/` folder if one exists.

**Step 3 — Choose Rigor**

- **nano**: ≤2 files, obvious path, no high-risk domain, user didn't ask for planning
- **lite**: low-risk feature, short plan useful, 1–3 conversations
- **standard**: multiple layers, >3 conversations, meaningful user-facing behavior
- **strict**: auth, payment, billing, secrets, privacy, schema migration, destructive data, compliance

Add `fast` only if user explicitly asks for no-pause execution. Never combine `strict` + `fast`.

**Step 4 — Ask Only If Unsafe**

Ask one clarifying question only if:
- Multiple active features could match
- A destructive request lacks a target
- Cannot infer intent between review, fix, or new implementation

Otherwise choose conservatively and proceed.

**Step 5 — Print Decision**

```
I will treat this as: <rigor>
Reason: <one sentence>
Starting: <plain-language next action>
```

**Step 6 — Invoke Route**

```
storm <topic>
team-flow <feature> nano
team-flow <feature> lite
team-flow <feature> standard
team-flow <feature> strict
team-flow <feature> build
team-flow <feature> test
review
retro <feature>
```

Default for new features: `team-flow <feature> lite`.

---

## Behavior: end

**Step 1 — Find in-progress feature**

Scan `plans/` (skip `.archive/`). For each feature folder, read `PROGRESS.md`.
Look for `status: IN PROGRESS` or `Status: IN PROGRESS`.

**Step 2 — If a feature is in progress**

Print:

```
Feature: <feature-name>
Conversations done / total: <X> / <Y>
```

Ask:

```
Write a retro? (y/n):
```

- **y**: invoke `retro <feature>`
- **n**: print `All done. Changes committed? Run git commit if not.`

**Step 3 — If no feature is in progress**

Print:

```
Nothing in progress. All done.
```

---

## Behavior: pause

Scan `plans/` for a feature whose `PROGRESS.md` contains `status: IN PROGRESS`.
If found, write `status: PAUSED` to that feature's `PROGRESS.md`.

Print:

```
Session paused. Resume with /pathly go when ready.
```

---

## Behavior: meet

Scan `plans/*/STATE.json` sorted by modification time (most recent first).
Pick the active feature and run the meet workflow: consult one relevant role,
write a read-only consult note to `plans/<feature>/feedback/CONSULT_<role>.md`.

---

## Behavior: help (default when $ARGUMENTS is empty)

**Step 1 — Detect state**

1. If `args` is provided, use it as `FEATURE`. Otherwise scan `plans/` for the
   most recently modified feature folder.
2. Read `plans/$FEATURE/PROGRESS.md` if it exists.
3. Check `plans/$FEATURE/feedback/` for open files.
4. Infer rigor: **lite** (4 required files only), **standard** (all 8 files),
   **strict** (8 files + audit markers), **unknown** (no plan folder).
5. Classify state:
   - **no-feature** — no plans/ folder or no feature found
   - **storm-done** — `plans/STORM_SEED.md` exists, no plans folder yet
   - **plan-done** — plans folder exists, conversations TODO, no open feedback
   - **feedback-open** — feedback file(s) present
   - **build-done** — all conversations DONE, no RETRO.md yet
   - **retro-done** — RETRO.md exists

**Step 2 — Print state-aware menu**

### no-feature

```
═══════════════════════════════════════════
  Pathly — No active feature found
═══════════════════════════════════════════

  [1] Start a new feature          /pathly go <what you want>
  [2] Brainstorm an unclear idea   /pathly go storm
  [3] Import a PRD/BMAD file       prd-import / bmad-import
  [4] See all commands

Reply with 1–4:
```

### plan-done

```
═══════════════════════════════════════════
  <feature>  |  Plan ready
  Conv: <X> done · <Y> remaining
  Rigor: <lite|standard|strict>
═══════════════════════════════════════════

  [1] Continue building            /pathly go continue
  [2] Run full pipeline            team-flow <feature> build
  [3] Review current code          review
  [4] See all commands

Reply with 1–4:
```

### feedback-open

```
═══════════════════════════════════════════
  <feature>  |  Open feedback requires action
  Rigor: <lite|standard|strict>
═══════════════════════════════════════════

  Open files:
    <list each file → who must act>

  [1] Resume pipeline              /pathly go continue
  [2] Show feedback file content
  [3] See all commands

Reply with 1–3:
```

### build-done

```
═══════════════════════════════════════════
  <feature>  |  All conversations complete
  Rigor: <lite|standard|strict>
═══════════════════════════════════════════

  [1] Close feature (tests + retro)  /pathly end
  [2] Run tests only                  team-flow <feature> test
  [3] Write retro only                retro <feature>
  [4] See all commands

Reply with 1–4:
```

### retro-done

```
═══════════════════════════════════════════
  <feature>  |  DONE ✓
  RETRO.md written
  Rigor: <lite|standard|strict>
═══════════════════════════════════════════

  [1] Archive this feature         archive <feature>
  [2] Promote lessons              lessons
  [3] Start next feature           /pathly go <what you want>
  [4] Read the retro

Reply with 1–4:
```

**Step 3 — Full command reference (shown on "See all commands")**

```
───────────────────────────────────────────
  ENTRY POINTS
───────────────────────────────────────────
  /pathly                    state-aware menu
  /pathly <intent>           Director routes immediately
  /pathly start              welcome menu
  /pathly go [intent]        Director — reads state, routes
  /pathly help [feature]     state-aware menu for a specific feature
  /pathly end                wrap up session, offer retro
  /pathly pause              save state, exit cleanly
  /pathly meet               consult a role on the active feature

───────────────────────────────────────────
  PIPELINE
───────────────────────────────────────────
  team-flow <feature>        full pipeline, default rigor
  team-flow <feature> nano   tiny change, ≤2 files
  team-flow <feature> lite   short plan, 1–3 conversations
  team-flow <feature> standard  full 8-file plan
  team-flow <feature> strict    audit gates, high-risk changes
  team-flow <feature> build     skip to build stage
  team-flow <feature> test      skip to test stage
  team-flow <feature> fast      no pause points

───────────────────────────────────────────
  INDIVIDUAL STAGES
───────────────────────────────────────────
  storm [topic]              brainstorm → STORM_SEED.md
  plan <feature> [rigor]     create plan files
  review                     audit staged changes
  retro <feature>            write RETRO.md + extract lessons
  lessons                    promote candidates → LESSONS.md
  archive <feature>          move to plans/.archive/
  prd-import <f> <file>      translate PRD → plan files
  bmad-import <f> <file>     translate BMAD PRD → plan files
  verify-state [feature]     check stale feedback, PROGRESS drift

───────────────────────────────────────────
  FEEDBACK FILES  (plans/<feature>/feedback/)
───────────────────────────────────────────
  ARCH_FEEDBACK.md    reviewer → architect  (BLOCKING)
  REVIEW_FAILURES.md  reviewer → builder
  IMPL_QUESTIONS.md   builder  → planner
  DESIGN_QUESTIONS.md builder  → architect
  TEST_FAILURES.md    tester   → builder
  HUMAN_QUESTIONS.md  any      → user (BLOCKED_ON_HUMAN)

───────────────────────────────────────────
  TELEMETRY
───────────────────────────────────────────
  pathly-tokens              show activity by feature (run in terminal)

═══════════════════════════════════════════
```
