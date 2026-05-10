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

```
pathly/
├── core/                        ← SINGLE SOURCE OF TRUTH (tool-agnostic)
│   ├── agents/                  ← Agent behavior contracts (no spawning syntax)
│   │   ├── architect.md
│   │   ├── builder.md
│   │   ├── director.md
│   │   ├── discoverer.md
│   │   ├── orchestrator.md
│   │   ├── planner.md
│   │   ├── po.md
│   │   ├── quick.md
│   │   ├── reviewer.md
│   │   ├── scout.md
│   │   ├── tester.md
│   │   └── web-researcher.md
│   ├── prompts/                 ← Skill logic in natural language (tool-agnostic)
│   │   ├── team-flow.md
│   │   ├── explore.md
│   │   ├── build.md
│   │   ├── review.md
│   │   ├── storm.md
│   │   └── ...
│   └── templates/               ← Plan file templates (PROGRESS, USER_STORIES, etc.)
│       └── plan/
│
├── adapters/                    ← THIN tool-specific wrappers (spawning syntax only)
│   ├── claude-code/             ← Adds Agent() tool calls
│   │   ├── agents/              ← Wraps core/agents/ with Agent() spawning syntax
│   │   └── skills/              ← SKILL.md files per skill (reads core/prompts/ + adds spawn)
│   ├── codex/                   ← Adds Agents SDK calls
│   │   └── skills/              ← SKILL.md files per skill (no agents/ — Codex reads natively)
│   └── cli/                     ← CLI adapter notes
│
│   NOTE: adapters/copilot/ is not yet built. Copilot cross-tool support is planned.
│
├── orchestrator/                ← Pure FSM library — rules only, no I/O (top-level package)
│   ├── reducer.py               ← Pure function: (state, event) → new_state
│   ├── state.py                 ← State data model
│   ├── events.py                ← Event types
│   ├── eventlog.py              ← Reads/writes event log file
│   ├── feedback.py              ← Feedback file handling
│   ├── agent_runner.py          ← Agent invocation contract
│   └── constants.py
│
├── pathly/                      ← Python package (CLI + hooks + runner)
│   ├── cli/                     ← pathly install, pathly help, pathly status (KEEP)
│   ├── hooks/                   ← Claude Code event hooks (KEEP)
│   ├── runners/                 ← Optional: external CLI execution
│   └── team_flow/               ← Python driver — uses orchestrator/ + runners (KEEP)
│       ├── manager.py           ← Main loop: read state → reduce → call runner → write event
│       ├── prompts.py           ← Builds prompts to send to Claude/Codex
│       └── filesystem.py        ← Manages plan file paths
│
└── docs/                        ← Documentation
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
pathly install
        │
        ├── adapters/claude-code/agents/**  ──────► ~/.claude/agents/
        │
        ├── adapters/claude-code/skills/**  ──────► ~/.claude/skills/
        │
        └── adapters/codex/skills/**        ──────► ~/.codex/skills/
```

For Claude Code: copy adapter files as-is (Markdown with Agent() calls).
For Codex: copy adapter files as-is (SKILL.md natural language, no slash commands).
For Copilot: **not yet implemented** — `adapters/copilot/` does not exist yet.

---

## Cross-tool compatibility

| Feature | Claude Code | Codex | Copilot |
|---|---|---|---|
| Agent behavior contracts | ✓ via ~/.claude/agents/ | ✓ via ~/.codex/agents/ | ✓ via AGENTS.md standard |
| Skills (SKILL.md) | ✓ native | ✓ native | ✓ native (Aug 2025) |
| Subagent spawning | Agent() tool | Agents SDK (MCP) | /fleet, /delegate |
| Natural language activation | /go skill + director | natural language | natural language |

**Key constraint:** Subagent spawning syntax is tool-specific. There is no universal standard.

**Copilot status:** Listed in the table above as a target but `adapters/copilot/` is not yet built.

**Solution (thin adapters):** `core/prompts/` contains the skill *logic* in natural language.
Adapters add only the tool-specific spawn call on top:

```
# core/prompts/team-flow.md
Delegate implementation to the builder agent.
Then delegate review to the reviewer agent.

# adapters/claude-code/skills/team-flow/SKILL.md (adds Agent() spawn calls)
Spawn Agent(subagent_type="builder") for implementation.
Spawn Agent(subagent_type="reviewer") for review.
```

---

## Python code — what to keep vs delete

| Module | Keep? | Reason |
|---|---|---|
| `pathly/cli/` | **YES** | `pathly install` — needed for setup |
| `pathly/hooks/` | **YES** | Claude Code event hooks — real automation value |
| `pathly/runners/` | **Optional** | Only if you want `pathly team-flow` as a terminal CLI |
| `pathly/orchestrator/` | **Keep as reference** | Pure FSM library — documents the state machine that orchestrator.md implements in natural language |
| `pathly/team_flow/` | **YES** | Python driver — keeps the terminal CLI path (`pathly team-flow`) alive |

### orchestrator/ vs team_flow/

**`pathly/orchestrator/`** — pure FSM library. No I/O, no side effects.
- `reducer.py` is a pure function: `(state, event) → new_state`
- Defines all state transitions, retry logic, feedback priority, state stack for nested blocking
- When the orchestrator agent reads `orchestrator.md`, it implements the same logic in natural language
- Worth keeping: auditable, testable, documents edge cases precisely

**`pathly/team_flow/`** — Python driver. Has side effects (file I/O, subprocess calls).
- `manager.py` reads STATE.json → calls reducer → calls claude runner → writes events → loops
- This is what wires orchestrator/ + runners/ + filesystem together
- Keeps the terminal CLI path alive: `pathly team-flow my-feature` works outside Claude Code
- Both paths coexist: skills (inside the tool) and team_flow (from terminal) share the same FSM logic via orchestrator/

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
