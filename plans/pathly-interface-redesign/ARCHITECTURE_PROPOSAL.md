# pathly-interface-redesign — Architecture Proposal

## Problem Statement

Two problems exist in the current architecture:

1. **Argument-based skill surface**: Skills take positional arguments (`pathly flow <feature>`, `pathly continue <feature>`). Users must remember argument syntax per platform. Argument parsing is duplicated across adapter skill files. The interface is not uniform across Claude Code, Codex, and Copilot.

2. **Duplicated behavioral contracts**: Adapter agent files (`adapters/claude/agents/architect.md`, etc.) copy the full behavioral content from `core/agents/architect.md`. There is no enforced single source of truth. When `core/agents/` is updated, adapters must be manually synced or they drift silently.

## Proposed Solution

### Part 1 — No-argument verb surface

Replace argument-based skills with five verb-based entry points. Arguments are replaced by file-reading (state from `STATE.json`) and interactive prompting. The same five verbs work on every platform.

```
/pathly start    → director (asks intent, infers or creates feature)
/pathly continue → orchestrator (reads STATE.json, resumes)
/pathly end      → orchestrator (confirms, triggers retro)
/pathly meet     → director (picks expert), then expert agent
/pathly help     → reads STATE.json, prints context-aware menu
```

### Part 2 — Install-time agent stitching

```
core/agents/architect.md           ← behavioral contract only (no spawn syntax)
        +
adapters/claude/_meta/architect.yaml  ← frontmatter + spawn section only
        ↓  (pathly install stitches at install time)
~/.claude/agents/architect.md      ← complete agent file (never committed to repo)
```

No generated files committed. The repo contains only sources. The install destination contains stitched artifacts.

## Layer Breakdown

```
User command
  /pathly [verb]
        │
        ▼
Skill layer — core/skills/pathly.md
  routes verb → target agent (no argument parsing)
        │
        ▼
Agent layer — ~/.claude/agents/<agent>.md (stitched at install)
  behavioral contract (from core/) + spawn syntax (from meta/)
        │
        ├──► director     → decides flow type, spawns orchestrator
        ├──► orchestrator → reads STATE.json, spawns workers
        ├──► builder      → implements, can spawn: [quick, scout]
        ├──► reviewer     → checks, can spawn: [quick, scout]
        └──► meet target  → reads-only, writes consult note
        │
        ▼
State layer — plans/<feature>/
  STATE.json, PROGRESS.md, feedback/, consults/
```

## Key Design Decisions

### Decision 1: No-argument skills — state from files, not CLI

- **Options considered**: (A) keep arguments, (B) no arguments + state from files, (C) hybrid (optional arguments)
- **Chosen**: B — no arguments
- **Rationale**: Pathly's first principle is "files are the protocol." State in CLI arguments breaks cross-session recovery. No-argument verbs make the interface identical across all platforms. Optional arguments (C) are tempting but create two code paths and re-introduce platform-specific parsing.

### Decision 2: Install-time stitching, not build-time committed generation

- **Options considered**: (A) committed generated files, (B) install-time stitching (no committed files), (C) YAML-only source with compile step
- **Chosen**: B — install-time stitching
- **Rationale**: Committed generated files drift when sources change. YAML-only (C) is bad for prose-heavy behavioral contracts — embedding markdown in YAML strings is unreadable. Install-time stitching keeps the repo clean, keeps prose in markdown, and puts generation where it belongs (the installer).

### Decision 3: `can_spawn` as content, not runtime enforcement

- **Options considered**: (A) runtime enforcement (installer validates spawns at runtime), (B) content injection (can_spawn injected into agent's system prompt)
- **Chosen**: B — content injection
- **Rationale**: Runtime enforcement requires a proxy layer around Agent() calls. Content injection is simpler: the agent's own system prompt tells it what it's allowed to spawn. This aligns with how Pathly works — the agent contract defines behavior, the agent follows it.

### Decision 4: director vs orchestrator for `/pathly start`

- **Options considered**: (A) `/pathly start` → orchestrator directly, (B) `/pathly start` → director → orchestrator
- **Chosen**: B — via director
- **Rationale**: Starting a flow requires a decision (scope, feature name, rigor). Director is the decision agent. Orchestrator is the execution agent. The separation of concerns is preserved.

### Decision 5: `/pathly continue` and `/pathly end` bypass director

- **Options considered**: (A) all verbs through director, (B) continue/end go directly to orchestrator
- **Chosen**: B — direct to orchestrator
- **Rationale**: `continue` and `end` require no decision — STATE.json already contains the active feature and phase. Adding director as an intermediary adds latency and a context window hit for no benefit.

## New Components

| Component | What it is | Layer |
|---|---|---|
| `core/skills/pathly.md` (updated) | No-argument verb router | Skill |
| `adapters/{platform}/_meta/{agent}.yaml` | Thin meta: frontmatter + spawn section | Adapter |
| `pathly/cli/stitch.py` | Reads meta YAML + core agent → stitched file | CLI/installer |
| `can_spawn` section in generated agent files | Capability boundary, content-injected | Generated agent |

## Capability Matrix

| Agent | can_spawn |
|---|---|
| orchestrator | all |
| director | orchestrator, architect, po, web-researcher |
| builder | quick, scout |
| reviewer | quick, scout |
| architect | quick, scout, web-researcher |
| planner | quick, scout |
| tester | quick, scout |
| po | none |
| web-researcher | none |
| scout | TERMINAL |
| quick | TERMINAL |

## Risks

- **Stitching errors are silent at author time**: A malformed meta YAML won't be caught until `pathly install` runs. Mitigation: add `pathly install --dry-run` that validates all meta files and reports errors before writing.
- **`/pathly start` without arguments feels ambiguous**: Users may not know what to type after. Mitigation: the director's first message is a clear prompt ("What do you want to build?"), not a blank cursor.
- **`installable-workflow-architecture` plan overlap**: That plan's Conv 2 covers adapter materialization. This plan's Conv 3 changes what gets materialized. Coordinate: this plan's Conv 3 should be done before `installable-workflow-architecture` Conv 2, or Conv 2 of that plan should be updated to use the stitcher.
- **Copilot spawn syntax unknown**: Copilot's `/fleet`, `/delegate` pattern is documented but not yet validated. Mitigation: Copilot meta files are created with a prose delegation fallback and marked `status: experimental`.
