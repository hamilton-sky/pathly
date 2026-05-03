# Framework Flow Diagram

---

## Full Lifecycle

```
  USER
   │
   │  /team-flow <feature>
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
║  │   hits requirement gap?                     │    ║
║  │   → IMPL_QUESTIONS.md → planner clarifies   │    ║
║  │                                             │    ║
║  │   hits technical blocker?                   │    ║
║  │   → DESIGN_QUESTIONS.md → architect fixes   │    ║
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
  (storm can read RETRO.md as seed)
```

---

## Feedback File Map

```
  reviewer ──► ARCH_FEEDBACK.md    ──► architect   BLOCKING
           └─► REVIEW_FAILURES.md  ──► builder

  builder  ──► IMPL_QUESTIONS.md   ──► planner
           └─► DESIGN_QUESTIONS.md ──► architect

  tester   ──► TEST_FAILURES.md    ──► builder

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
  /team-flow <feature>          full pipeline from discovery
  /team-flow <feature> plan     skip discovery → start at plan
  /team-flow <feature> build    skip discovery+plan → resume build
  /team-flow <feature> test     skip to test stage only
  /team-flow <feature> fast     full pipeline, no pause points
  /team-flow <feature> build fast  resume build, no pauses

  /help [feature]               detect state → show numbered actions
  /archive <feature>            close out a completed feature
```
