# Pathly Architecture

> Canonical reference for the simplified Pathly architecture.
> Reflects decisions made after the May 2026 architecture review.

---

## What Pathly is

Pathly is a multi-agent workflow system that sits on top of AI coding tools (Claude Code, Codex, Copilot). It provides:
- **Agent behavior contracts** — role definitions for specialized workers
- **Skills** — user-invocable workflow commands (slash commands)
- **An FSM orchestrator** — deterministic workflow state management
- **An installer** — copies agents and skills into each tool's expected location

The user installs Pathly once. After that, they interact with their AI coding tool normally — the tool reads Pathly's agents and skills transparently.

---

## Folder structure

This is a **monorepo** containing two pip packages plus shared docs and plans.

```
pathly/                              ← monorepo root (pyproject: pathly-monorepo)
│
├── pathly-adapters/                 ← pip package: pathly-adapters
│   │                                   installs via: pip install -e pathly-adapters/
│   │                                   CLI entry: pathly-setup
│   │
│   ├── core/                        ← SINGLE SOURCE OF TRUTH (tool-agnostic)
│   │   ├── agents/                  ← Agent behavior contracts (.md — no spawning syntax)
│   │   │   ├── architect.md
│   │   │   ├── builder.md
│   │   │   ├── director.md
│   │   │   ├── orchestrator.md
│   │   │   ├── planner.md
│   │   │   ├── po.md
│   │   │   ├── quick.md
│   │   │   ├── reviewer.md
│   │   │   ├── scout.md
│   │   │   ├── tester.md
│   │   │   └── web-researcher.md
│   │   ├── skills/                  ← Skill logic in natural language (tool-agnostic .md)
│   │   │   ├── team-flow.md
│   │   │   ├── explore.md
│   │   │   ├── build.md
│   │   │   ├── review.md
│   │   │   ├── storm.md
│   │   │   └── ...
│   │   └── templates/               ← Plan file templates (PROGRESS, USER_STORIES, etc.)
│   │       └── plan/
│   │
│   ├── adapters/                    ← Thin tool-specific wrappers
│   │   ├── claude/                  ← .claude-plugin/ + _meta/*.yaml per agent/skill
│   │   ├── codex/                   ← .codex-plugin/ + _meta/*.yaml per agent/skill
│   │   └── copilot/                 ← _meta/*.yaml per agent/skill
│   │
│   └── install_cli/                 ← Python CLI: detects host tools, stitches + deploys files
│       ├── detect.py                ← Discovers installed AI tools
│       ├── stitch.py                ← Combines core/ + adapter _meta/ into deployable files
│       ├── materialize.py           ← Writes output files to ~/.claude/, ~/.codex/, etc.
│       └── setup_command.py         ← Entry point for pathly-setup command
│
├── pathly-engine/                   ← pip package: pathly-engine
│   │                                   installs via: pip install -e pathly-engine/
│   │                                   CLI entry: pathly
│   │
│   ├── orchestrator/                ← Pure FSM library — rules only, no I/O
│   │   ├── reducer.py               ← Pure function: (state, event) → new_state
│   │   ├── state.py                 ← State data model
│   │   ├── events.py                ← Event types
│   │   ├── eventlog.py              ← Reads/writes event log file
│   │   ├── feedback.py              ← Feedback file handling
│   │   ├── agent_runner.py          ← Agent invocation contract
│   │   └── constants.py
│   │
│   ├── runners/                     ← External CLI execution (claude, codex)
│   │   ├── base.py
│   │   ├── claude.py
│   │   └── codex.py
│   │
│   ├── team_flow/                   ← Python driver — uses orchestrator/ + runners
│   │   ├── manager.py               ← Main loop: read state → reduce → call runner → write event
│   │   ├── prompts.py               ← Builds prompts to send to Claude/Codex
│   │   ├── filesystem.py            ← Manages plan file paths
│   │   └── config.py
│   │
│   └── engine_cli/                  ← CLI entry point (exposes `pathly` command)
│
├── .agents/                         ← Codex marketplace metadata
│   └── plugins/marketplace.json
│
├── docs/                            ← Documentation
├── plans/                           ← Feature plans (runtime state per project)
├── tests/                           ← Root-level integration tests
├── install.sh / install.ps1         ← Bootstrap installers
└── AGENTS.md                        ← Root agent/skill wiring for this repo
```

---

## Skills vs Agents

| | Agent | Skill |
|---|---|---|
| **What it is** | Role/persona with behavior contract | User-invocable workflow command |
| **Who triggers it** | Orchestrator or other agents | User directly (`/skill-name`) |
| **Lives in** | `core/agents/` | `core/skills/` |
| **Format** | Markdown behavior contract | SKILL.md (YAML frontmatter + instructions) |
| **Example** | builder, reviewer, scout | /team-flow, /explore, /review |

**Analogy:** agents are workers with job descriptions. Skills are the workflows that hire and coordinate those workers.

---

## Agent hierarchy

```
Orchestrator (top-level — spawns all)
├── architect       → no subagents (uses tools directly)
├── planner         → no subagents
├── builder         → spawns: quick, scout (read-only, before implementing)
├── reviewer        → spawns: quick, scout (for consistency checks)
├── tester          → no subagents
├── po              → no subagents
├── web-researcher  → no subagents
├── discoverer      → no subagents
├── scout           → TERMINAL (cannot spawn)
└── quick           → TERMINAL (cannot spawn)
```

**quick vs scout:**
- `quick` — 1-2 tool calls, single factual lookup, inline answer, no report format
- `scout` — 5-15 tool calls, cross-file investigation, structured Findings/Recommendation/Ambiguities report

---

## How the runtime flow works

```
User types: /team-flow my-feature
        │
        ▼
Tool reads: ~/.claude/skills/team-flow/SKILL.md   (or ~/.codex/skills/...)
        │
        ▼
Skill instructs Claude to act as orchestrator
        │
        ▼
Orchestrator reads:
  plans/my-feature/STATE.json     ← current workflow phase
  plans/my-feature/PROGRESS.md   ← what is done
  plans/my-feature/feedback/     ← any blockers?
        │
        ▼
Orchestrator spawns agents via Agent() tool (fresh context window per agent):
  Agent(subagent_type="builder") → reads ~/.claude/agents/builder.md → implements
  Agent(subagent_type="reviewer") → reads ~/.claude/agents/reviewer.md → checks
  Agent(subagent_type="tester") → reads ~/.claude/agents/tester.md → verifies
        │
        ▼
Results written back to plans/my-feature/
Orchestrator reads state again → spawns next agent → loop until done
```

Each spawned agent gets a **fresh context window** — only the task prompt and its behavior contract are in context. The orchestrator context stays small (state + results only).

---

## How pathly install works

```
pathly-setup
        │
        ├── detect.py detects which tools are installed
        │
        ├── stitch.py merges core/ + adapters/<tool>/_meta/*.yaml
        │       into deployable agent and skill files
        │
        ├── materialize.py writes stitched files:
        │   ├── adapters/claude/_meta/**  ──────► ~/.claude/agents/ + ~/.claude/skills/
        │   ├── adapters/codex/_meta/**   ──────► ~/.codex/agents/ + ~/.codex/skills/
        │   └── adapters/copilot/_meta/** ──────► Copilot workspace config
        │
        └── setup_command.py is the CLI entry point (registered as `pathly-setup`)
```

For Claude Code: stitched files include Agent() spawn calls, deployed to `~/.claude/`.
For Codex: stitched files use natural language skill prompts, deployed to `~/.codex/`.
For Copilot: stitched files use Copilot-compatible format, deployed to workspace config.

---

## Cross-tool compatibility

| Feature | Claude Code | Codex | Copilot |
|---|---|---|---|
| Agent behavior contracts | ✓ via ~/.claude/agents/ | ✓ via ~/.codex/agents/ | ✓ via AGENTS.md standard |
| Skills (SKILL.md) | ✓ native | ✓ native | ✓ native (Aug 2025) |
| Subagent spawning | Agent() tool | Agents SDK (MCP) | /fleet, /delegate |
| Natural language activation | /go skill + director | natural language | natural language |

**Key constraint:** Subagent spawning syntax is tool-specific. There is no universal standard.

**Solution (thin adapters):** `core/skills/` contains the skill *logic* in natural language.
Each adapter's `_meta/*.yaml` adds only the tool-specific spawn call on top:

```
# core/skills/team-flow.md
Delegate implementation to the builder agent.
Then delegate review to the reviewer agent.

# adapters/claude/_meta/go_skill.yaml  (adds Agent() spawn calls for Claude Code)
Spawn Agent(subagent_type="builder") for implementation.
Spawn Agent(subagent_type="reviewer") for review.
```

---

## Python packages — what each does

### pathly-adapters (`pathly-setup` command)

| Module | Purpose |
|---|---|
| `install_cli/detect.py` | Discovers which AI tools (Claude Code, Codex, Copilot) are installed |
| `install_cli/stitch.py` | Merges `core/` content with adapter `_meta/*.yaml` into deployable files |
| `install_cli/materialize.py` | Writes stitched output to `~/.claude/`, `~/.codex/`, etc. |
| `install_cli/setup_command.py` | CLI entry point registered as `pathly-setup` |
| `core/` | Source-of-truth agent contracts, skill logic, plan templates — never edited by install |
| `adapters/` | Per-tool YAML metadata (`_meta/`) and plugin manifests |

### pathly-engine (`pathly` command)

| Module | Purpose |
|---|---|
| `orchestrator/` | Pure FSM library — `reducer.py` is `(state, event) → new_state`, no I/O |
| `runners/` | External subprocess runners for Claude Code and Codex CLI |
| `team_flow/` | Python driver that wires orchestrator + runners + filesystem for terminal use |
| `engine_cli/` | CLI entry point registered as `pathly` |

### orchestrator/ vs team_flow/

**`orchestrator/`** — pure FSM library. No I/O, no side effects.
- `reducer.py` is a pure function: `(state, event) → new_state`
- Defines all state transitions, retry logic, feedback priority, state stack for nested blocking
- When the orchestrator agent reads `orchestrator.md`, it implements the same logic in natural language
- Auditable and testable; documents edge cases precisely

**`team_flow/`** — Python driver. Has side effects (file I/O, subprocess calls).
- `manager.py` reads STATE.json → calls reducer → calls runner → writes events → loops
- Wires orchestrator/ + runners/ + filesystem together
- Keeps the terminal CLI path alive: `pathly team-flow my-feature` works outside Claude Code

---

## Natural language activation

Instead of terminal commands, the user speaks naturally inside their tool:

```
User: "I want to build user authentication"
        │
        ▼
director agent reads request → classifies → chooses scope (nano/lite/standard/strict)
        │
        ▼
Routes to /team-flow automatically
        │
        ▼
Workflow starts — user never typed a command
```

Set up in CLAUDE.md / AGENTS.md:
```
For new feature requests, route through the director agent first.
```

---

## What Pathly is NOT

- Not a standalone process — it runs inside the AI coding tool
- Not a replacement for Claude Code / Codex / Copilot — it extends them
- Not a Python service — the Python package is only for installation and hooks
- Not a conversation manager — context isolation is handled by Agent() (Claude Code) or equivalent
