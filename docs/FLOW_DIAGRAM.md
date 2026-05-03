# Framework Flow Diagram

---

## Full Lifecycle

```
  USER
   │
   │  /go                   ← prompts "What do you want?" then routes
   │  /go <plain English>   ← skip the prompt, routes immediately
   │  /team-flow <feature>  ← direct pipeline entry (power users)
   ▼
╔══════════════════════════════════════╗
║  STAGE 0 — Discovery Path           ║
║                                     ║
║  [1] Quick storm                    ║
║  [2] Skip discovery                 ║
║  [3] Import PRD                     ║
╚══════════════════════════════════════╝
   │         │              │
  [1]       [2]            [3]
   │         │              │
   ▼         │              ▼
╔════════╗   │    ╔══════════════════╗
║ STORM  ║   │    ║  /prd-import     ║
║ arch.  ║   │    ║  reads PRD file  ║
║ (opus) ║   │    ║  → 8 plan files  ║
╚════════╝   │    ╚══════════════════╝
   │         │              │
   │         │    (skips stages 1+2)
   ▼         ▼              │
╔══════════════════════════╗│
║  STAGE 2 — Plan          ║│
║  planner (sonnet)        ║│
║  → plans/<feature>/      ║│
║    USER_STORIES.md       ║│
║    IMPLEMENTATION_PLAN.md║│
║    PROGRESS.md           ║│
║    CONVERSATION_PROMPTS  ║│
║    HAPPY_FLOW.md         ║│
║    EDGE_CASES.md         ║│
║    ARCHITECTURE_PROPOSAL ║│
║    FLOW_DIAGRAM.md       ║│
╚══════════════════════════╝│
   │         ◄──────────────┘
   │  PAUSE: "Review plan. go / stop"
   ▼
╔══════════════════════════════════════════════════════╗
║  STAGE 3 — Implement + Review Loop                   ║
║                                                      ║
║  for each TODO conversation in PROGRESS.md:          ║
║                                                      ║
║  ┌─────────────────────────────────────────────┐    ║
║  │ builder (sonnet)                             │    ║
║  │   implements conversation N                 │    ║
║  │   updates PROGRESS.md                       │    ║
║  │                                             │    ║
║  │   hits requirement gap? [REQ]               │    ║
║  │   → IMPL_QUESTIONS.md → planner clarifies   │    ║
║  │                                             │    ║
║  │   hits technical blocker? [ARCH]            │    ║
║  │   → DESIGN_QUESTIONS.md → architect fixes   │    ║
║  │                                             │    ║
║  │   unclear which? [UNSURE] → both files      │    ║
║  └──────────────────┬──────────────────────────┘    ║
║                     │                               ║
║                     ▼                               ║
║  ┌─────────────────────────────────────────────┐    ║
║  │ reviewer (sonnet)                            │    ║
║  │   checks .claude/rules/ contracts            │    ║
║  │                                             │    ║
║  │   architectural violation?                  │    ║
║  │   → ARCH_FEEDBACK.md → architect (BLOCKING) │    ║
║  │     architect redesigns → builder rebuilds  │    ║
║  │                                             │    ║
║  │   implementation violation?                 │    ║
║  │   → REVIEW_FAILURES.md → builder fixes      │    ║
║  │     builder fixes → reviewer re-checks      │    ║
║  │                                             │    ║
║  │   PASS → advance to next conversation       │    ║
║  └─────────────────────────────────────────────┘    ║
║                                                      ║
║  max 2 retry cycles per conversation                 ║
║  exceeded → STOP, surface to user                    ║
╚══════════════════════════════════════════════════════╝
   │
   │  PAUSE: "Commit. continue / stop"
   ▼
╔══════════════════════════════════════════════════════╗
║  STAGE 4 — Test + Fix Loop                           ║
║                                                      ║
║  ┌─────────────────────────────────────────────┐    ║
║  │ tester (sonnet)                              │    ║
║  │   reads USER_STORIES.md                     │    ║
║  │   maps each AC: PASS / FAIL / NOT COVERED   │    ║
║  │                                             │    ║
║  │   any failures?                             │    ║
║  │   → TEST_FAILURES.md → builder fixes        │    ║
║  │     builder fixes → tester re-checks        │    ║
║  │                                             │    ║
║  │   all PASS → proceed                        │    ║
║  └─────────────────────────────────────────────┘    ║
║                                                      ║
║  max 2 retry cycles → STOP, surface to user          ║
╚══════════════════════════════════════════════════════╝
   │
   │  PAUSE: "All ACs pass. done?"
   ▼
╔══════════════════════════════════════╗
║  STAGE 5 — Retro                    ║
║  quick (haiku)                      ║
║  → plans/<feature>/RETRO.md         ║
║    what worked / what didn't        ║
║    seed for next storm              ║
║  → LESSONS_CANDIDATE.md (append)    ║
║    extracted patterns from retro    ║
╚══════════════════════════════════════╝
   │
   │  (optional, run after 2+ retros)
   ▼
╔══════════════════════════════════════╗
║  /lessons                           ║
║  reads: LESSONS_CANDIDATE.md        ║
║         plans/.archive/*/RETRO.md   ║
║  promotes patterns from 2+ features ║
║  → LESSONS.md (max 12 active)       ║
║  planner reads this before /plan    ║
╚══════════════════════════════════════╝
   │
   ▼
╔══════════════════════════════════════╗
║  /archive <feature>                 ║
║  validates: RETRO.md + all DONE     ║
║  moves: plans/<feature>/            ║
║      → plans/.archive/<feature>/   ║
║  recoverable: git checkout          ║
╚══════════════════════════════════════╝
   │
   ▼
  NEXT FEATURE
  /team-flow <new-feature>
  (planner applies LESSONS.md injections)
  (storm can read RETRO.md as seed)
```

---

## Feedback File Map

```
  reviewer ──► ARCH_FEEDBACK.md    ──► architect   BLOCKING
           └─► REVIEW_FAILURES.md  ──► builder

  builder  ──► IMPL_QUESTIONS.md   ──► planner      [REQ] questions
           └─► DESIGN_QUESTIONS.md ──► architect    [ARCH] questions
           (both if [UNSURE] — correct owner discards)

  tester   ──► TEST_FAILURES.md    ──► builder

  any      ──► HUMAN_QUESTIONS.md  ──► user         (V2 — not yet wired)
               unresolvable by any agent → pipeline blocks, user resolves in chat

  File present = issue open
  File deleted = resolved
  Max 2 cycles per conversation before hard stop
```

---

## Agent + Model Map

```
  architect   ── opus   ──  design, trade-offs, resolves ARCH + DESIGN files
  planner     ── sonnet ──  stories, scope, resolves IMPL_QUESTIONS
  builder     ── sonnet ──  implementation, fixes REVIEW + TEST failures
  reviewer    ── sonnet ──  adversarial check, writes ARCH + REVIEW files
  tester      ── sonnet ──  AC verification, writes TEST_FAILURES
  discoverer  ── sonnet ──  live site tracing, POM generation
  orchestrator── haiku  ──  pipeline sequencing, feedback routing
  quick       ── haiku  ──  retro, fast lookups
```

---

## Entry Points

```
  ┌─────────────────────────────────────────────────────┐
  │  NEW USER                                           │
  │                                                     │
  │  /help                                              │
  │    → [1] Describe what you want (plain English)     │
  │    → asks: "What do you want to build?"             │
  │    → /go <answer>                                   │
  │         → reads project state                       │
  │         → classifies intent                         │
  │         → confirms route                            │
  │         → /team-flow <feature>                      │
  └─────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────┐
  │  POWER USER                                         │
  │                                                     │
  │  /go                            ← prompts then routes│
  │  /go I want to add user auth    ← routes immediately │
  │  /team-flow <feature>           ← direct entry      │
  │  /team-flow <feature> build     ← resume build      │
  │  /team-flow <feature> test      ← test only         │
  │  /team-flow <feature> fast      ← no pause points   │
  │  /team-flow <feature> build fast                    │
  └─────────────────────────────────────────────────────┘

  /help [feature]               detect state → numbered menu
  /archive <feature>            close out a completed feature
  /lessons                      promote candidate lessons → LESSONS.md
```
