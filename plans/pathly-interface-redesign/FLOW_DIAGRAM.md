# pathly-interface-redesign — Flow Diagram

## Skill Entry Point Flow

```
User types: /pathly [verb]
        │
        ▼
core/skills/pathly.md (verb router)
        │
        ├── start  ──────────► director agent
        │                           │
        │                           ▼
        │                      asks intent
        │                           │
        │                           ▼
        │                      spawns orchestrator
        │                           │
        │                           ▼
        │                      orchestrator reads
        │                      plans/<f>/STATE.json
        │                           │
        │                    ┌──────┴──────┐
        │                    │  flow loop  │
        │                    └──────┬──────┘
        │                           ▼
        │               [builder|reviewer|tester...]
        │
        ├── continue ─────────► orchestrator
        │                      reads STATE.json
        │                      resumes from last state
        │
        ├── end ──────────────► orchestrator
        │                      confirms w/ user
        │                      routes to retro
        │
        ├── meet ─────────────► reads STATE.json
        │                      shows role menu
        │                           │
        │                    ┌──────┴─────────┐
        │                    │ architect       │
        │                    │ planner         │
        │                    │ reviewer        │
        │                    │ tester          │
        │                    │ scout           │
        │                    └──────┬─────────┘
        │                           │
        │                   writes consult note
        │                   plans/<f>/consults/
        │
        └── help ─────────────► reads STATE.json
                               prints state-aware menu
```

## Agent Stitching Flow (Install Time)

```
pathly install
        │
        ├── for each agent in core/agents/*.md
        │         │
        │         ├── read core/agents/{agent}.md
        │         │   (behavioral contract, no spawn syntax)
        │         │
        │         ├── read adapters/{platform}/_meta/{agent}.yaml
        │         │   (frontmatter + can_spawn + spawn_section)
        │         │
        │         ▼
        │   stitch:
        │   ┌──────────────────────────────┐
        │   │ --- (frontmatter from meta)  │
        │   │ name: architect              │
        │   │ model: opus                  │
        │   │ can_spawn: [quick, scout]    │
        │   │ ---                          │
        │   │                              │
        │   │ [behavioral contract         │
        │   │  from core/agents/]          │
        │   │                              │
        │   │ ## Sub-agent invocation      │
        │   │ [spawn_section from meta]    │
        │   └──────────────────────────────┘
        │         │
        │         ▼
        │   write to:
        │   ~/.claude/agents/{agent}.md
        │   ~/.codex/agents/{agent}.md
        │   (never committed to repo)
        │
        └── report: N agents stitched, M warnings
```

## Agent Capability Matrix (can_spawn)

```
orchestrator ──► all agents
        │
director ──────► orchestrator
               ► architect
               ► po
               ► web-researcher
        │
builder ───────► quick
               ► scout
        │
reviewer ──────► quick
               ► scout
        │
architect ─────► quick
               ► scout
               ► web-researcher
        │
planner ───────► quick
               ► scout
        │
tester ────────► quick
               ► scout
        │
po ────────────► [TERMINAL]
web-researcher ► [TERMINAL]
scout ─────────► [TERMINAL]
quick ─────────► [TERMINAL]
```

## State File Layout

```
plans/<feature>/
├── STATE.json        ← FSM state (used by continue/end/help)
├── EVENTS.jsonl      ← append-only event log
├── PROGRESS.md       ← conversation status table
├── feedback/
│   ├── REVIEW_FAILURES.md    → builder
│   ├── ARCH_FEEDBACK.md      → architect
│   ├── IMPL_QUESTIONS.md     → planner
│   ├── DESIGN_QUESTIONS.md   → architect
│   ├── TEST_FAILURES.md      → builder
│   └── HUMAN_QUESTIONS.md    → user
└── consults/
    └── 20260510-143022-architect.md  ← /pathly meet output
```
