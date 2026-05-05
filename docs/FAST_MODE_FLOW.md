# Fast Mode Flow — `/team-flow <feature> fast`

All human pause points between stages are skipped. `HumanResponseEvent("auto-advance")` is logged at each skipped gate. Hard stops (stalls, retry limits, `HUMAN_QUESTIONS.md`) still block the pipeline.

---

## ASCII Flow

```
/team-flow <feature> fast
         │
         ▼
╔══════════════════════════════════════╗
║  STAGE 0 — Discovery Path           ║
║  [1] Quick storm                    ║
║  [2] Skip discovery                 ║
║  [3] Import PRD                     ║
╚══════════════════════════════════════╝
         │  (user picks path once — only interactive moment)
         ▼
╔══════════════════════════════════════╗
║  STAGE 1 — Storm (if path 1)        ║
║  architect (opus)                   ║
╚══════════════════════════════════════╝
         │
         │  ⚡ AUTO-ADVANCE (no pause)
         ▼
╔══════════════════════════════════════╗
║  STAGE 2 — Plan                     ║
║  planner (sonnet)                   ║
║  → 8 plan files in plans/<feature>/ ║
╚══════════════════════════════════════╝
         │
         │  ⚡ AUTO-ADVANCE (no pause)
         ▼
╔══════════════════════════════════════════════════════════╗
║  STAGE 3 — Implement + Review Loop (repeats per conv)   ║
║                                                          ║
║  ┌───────────────────────────────────────────────────┐  ║
║  │  builder (sonnet) — conv N                        │  ║
║  └───────────────┬───────────────────────────────────┘  ║
║                  │                                       ║
║         requirement gap? ──► IMPL_QUESTIONS.md           ║
║                  │              planner resolves         ║
║         tech blocker?   ──► DESIGN_QUESTIONS.md          ║
║                  │              architect resolves       ║
║                  ▼                                       ║
║  ┌───────────────────────────────────────────────────┐  ║
║  │  reviewer (sonnet)                                │  ║
║  └───────────────┬───────────────────────────────────┘  ║
║                  │                                       ║
║         arch violation? ──► ARCH_FEEDBACK.md             ║
║                  │              architect → builder      ║
║         impl violation? ──► REVIEW_FAILURES.md           ║
║                  │              builder → zero-diff chk  ║
║                  │                                       ║
║         zero diff? ─────► HUMAN_QUESTIONS.md [STALL] ◄──║──┐
║                  │         🛑 PIPELINE STOPS HERE        ║  │
║                  │                                       ║  │
║         retry > 2? ────── escalate → same STALL ─────── ║──┘
║                  │                                       ║
║                  │  PASS                                 ║
║                  ▼                                       ║
║         ⚡ AUTO-ADVANCE — next conv                      ║
╚══════════════════════════════════════════════════════════╝
         │
         │  ⚡ AUTO-ADVANCE (no pause)
         ▼
╔══════════════════════════════════════════════════════════╗
║  STAGE 4 — Test + Fix Loop                              ║
║                                                          ║
║  ┌───────────────────────────────────────────────────┐  ║
║  │  tester (sonnet)                                  │  ║
║  │  maps every AC → PASS / FAIL / NOT COVERED        │  ║
║  └───────────────┬───────────────────────────────────┘  ║
║                  │                                       ║
║         failures? ──► TEST_FAILURES.md → builder fixes   ║
║                  │    builder → tester re-checks         ║
║                  │    retry > 2? → 🛑 STOP               ║
║                  │                                       ║
║                  │  all PASS                             ║
║                  ▼                                       ║
║         ⚡ AUTO-ADVANCE (no pause)                       ║
╚══════════════════════════════════════════════════════════╝
         │
         ▼
╔══════════════════════════════════════╗
║  STAGE 5 — Retro                    ║
║  quick (haiku)                      ║
║  → RETRO.md + LESSONS_CANDIDATE.md  ║
╚══════════════════════════════════════╝
         │
         ▼
       DONE ✓


Legend:
  ⚡ AUTO-ADVANCE   = pause skipped, HumanResponseEvent("auto-advance") logged
  🛑 PIPELINE STOPS = hard stops that survive fast mode
```

---

## Mermaid Diagram

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#e3f2fd', 'edgeLabelBackground':'#ffffff'}}}%%
graph TD
    Start((START)) --> CMD["⚡ /team-flow feature fast"]
    CMD --> DISCO["STAGE 0 — Discovery\nUser picks path 1 / 2 / 3\n🧑 Only interactive moment"]

    DISCO -->|"path 1"| STORM["STAGE 1 — Storm\n🤖 architect (opus)"]
    DISCO -->|"path 2"| PLAN
    DISCO -->|"path 3"| IMPORT["📥 /prd-import\nreads PRD file"]

    STORM -->|"⚡ auto-advance"| PLAN["STAGE 2 — Plan\n🤖 planner (sonnet)\n→ 8 plan files"]
    IMPORT -->|"skips stages 1+2"| BUILD

    PLAN -->|"⚡ auto-advance"| BUILD

    subgraph Loop ["STAGE 3 — Implement + Review Loop  (repeats per conversation)"]
        BUILD["🤖 builder (sonnet)\nconv N"] -->|"req gap"| IQ["IMPL_QUESTIONS.md\n→ planner resolves"]
        BUILD -->|"tech block"| DQ["DESIGN_QUESTIONS.md\n→ architect resolves"]
        IQ --> BUILD
        DQ --> BUILD
        BUILD --> REVIEW["🤖 reviewer (sonnet)"]
        REVIEW -->|"arch violation"| AF["ARCH_FEEDBACK.md\n→ architect → builder"]
        REVIEW -->|"impl violation"| RF["REVIEW_FAILURES.md\n→ builder fixes"]
        AF --> BUILD
        RF --> ZDIFF{"zero diff?"}
        ZDIFF -->|"yes"| STALL[["🛑 STALL\nHUMAN_QUESTIONS.md\nPIPELINE STOPS"]]
        ZDIFF -->|"no"| REVIEW
        REVIEW -->|"retry > 2"| STALL
        REVIEW -->|"⚡ PASS → auto-advance"| NEXT["next conv or exit loop"]
    end

    NEXT -->|"⚡ auto-advance"| TEST

    subgraph Testing ["STAGE 4 — Test + Fix Loop"]
        TEST["🤖 tester (sonnet)\nAC → PASS / FAIL / NOT COVERED"] -->|"failures"| TF["TEST_FAILURES.md\n→ builder fixes"]
        TF --> TEST
        TEST -->|"retry > 2"| STOP2[["🛑 STOP\nManual intervention"]]
        TEST -->|"⚡ all PASS → auto-advance"| DONE_TEST["exit test loop"]
    end

    DONE_TEST -->|"⚡ auto-advance"| RETRO["STAGE 5 — Retro\n🤖 quick summary\n→ retro skill writes RETRO.md"]
    RETRO --> End((DONE ✓))

    classDef stop fill:#ffcdd2,stroke:#c62828,stroke-width:3px;
    classDef auto fill:#f1f8e9,stroke:#558b2f,stroke-width:2px;
    classDef human fill:#fff9c4,stroke:#fbc02d,stroke-width:3px;

    class STALL,STOP2 stop;
    class STORM,PLAN,BUILD,REVIEW,TEST,RETRO auto;
    class DISCO human;
```
