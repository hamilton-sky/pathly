# Pathly Engine Architecture

> Canonical reference for the pathly-engine package.
> Reflects decisions made after the May 2026 architecture review.

---

## What pathly-engine Is

pathly-engine is the FSM runtime and CLI for the Pathly agent workflow system.
It provides:
- **An FSM orchestrator** — deterministic workflow state management
- **Subprocess runners** — invoke Claude Code and Codex CLI processes
- **A Python team-flow driver** — wires orchestrator + runners for terminal use
- **The `pathly` CLI** — stable local contract for init, status, doctor, flow

The `pathly` command does **not** spawn AI agents by itself. It writes filesystem
state that Claude Code or Codex reads and acts on, and runs the full team-flow
loop when runners are available.

---

## Folder Structure

```
pathly-engine/                   ← pip package: pathly-engine
│                                   installs via: pip install -e pathly-engine/
│                                   CLI entry: pathly
│
├── orchestrator/                ← Pure FSM library — rules only, no I/O
│   ├── reducer.py               ← Pure function: (state, event) → new_state
│   ├── state.py                 ← State data model
│   ├── events.py                ← Event types
│   ├── eventlog.py              ← Reads/writes event log file
│   ├── feedback.py              ← Feedback file handling
│   ├── agent_runner.py          ← Agent invocation contract
│   └── constants.py
│
├── runners/                     ← External CLI execution (claude, codex)
│   ├── base.py
│   ├── claude.py
│   └── codex.py
│
├── team_flow/                   ← Python driver — uses orchestrator/ + runners
│   ├── manager.py               ← Main loop: read state → reduce → call runner → write event
│   ├── prompts.py               ← Builds prompts to send to Claude/Codex
│   ├── filesystem.py            ← Manages plan file paths
│   └── config.py
│
└── engine_cli/                  ← CLI entry point (exposes `pathly` command)
```

---

## orchestrator/ vs team_flow/

**`orchestrator/`** — pure FSM library. No I/O, no side effects.
- `reducer.py` is a pure function: `(state, event) → new_state`
- Defines all state transitions, retry logic, feedback priority, state stack for nested blocking
- When the orchestrator agent reads `orchestrator.md`, it implements the same logic in natural language
- Auditable and testable; documents edge cases precisely

**`team_flow/`** — Python driver. Has side effects (file I/O, subprocess calls).
- `manager.py` reads `STATE.json` → calls reducer → calls runner → writes events → loops
- Wires orchestrator/ + runners/ + filesystem together
- Keeps the terminal CLI path alive: `pathly flow my-feature` works outside Claude Code

---

## Agent Spawning

How the runtime flow works:

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

Each spawned agent gets a **fresh context window** — only the task prompt and its
behavior contract are in context. The orchestrator context stays small (state +
results only).

Agent hierarchy:

```
Orchestrator (top-level — spawns all)
├── architect       → no subagents (uses tools directly)
├── planner         → no subagents
├── builder         → spawns: quick, scout (read-only, before implementing)
├── reviewer        → spawns: quick, scout (for consistency checks)
├── tester          → no subagents
├── po              → no subagents
├── web-researcher  → no subagents
├── scout           → TERMINAL (cannot spawn)
└── quick           → TERMINAL (cannot spawn)
```

---

## STATE.json Layout

`STATE.json` is a checkpoint. Disk recovery wins if `STATE.json` disagrees with
feedback files or `PROGRESS.md`.

```json
{
  "feature": "my-feature",
  "state": "BUILDING",
  "mode": "interactive",
  "rigor": "lite",
  "currentConversation": 2,
  "retryCountByKey": {
    "event-evt-abc123:REVIEW_FAILURES.md": 1
  },
  "stateStack": [],
  "activeFeedbackFile": null,
  "activeTarget": "builder",
  "lastActor": "reviewer"
}
```

`EVENTS.jsonl` is append-only. Each line records event, previous state, next
state, selected action, timestamp, and stack:

```jsonl
{"ts":"2026-05-11T10:00:00Z","event":"FILE_CREATED","file":"REVIEW_FAILURES.md","prev":"REVIEWING","next":"BLOCKED_ON_FEEDBACK","action":"spawn(builder)","stack":["REVIEWING"],"retry_key":"event-evt-abc123:REVIEW_FAILURES.md","retries":1}
```

---

## File-Based Protocol

Plans and workflow state all live on disk under `plans/<feature>/`:

```text
plans/<feature>/
|-- USER_STORIES.md
|-- IMPLEMENTATION_PLAN.md
|-- PROGRESS.md
|-- CONVERSATION_PROMPTS.md
|-- HAPPY_FLOW.md                 # standard/strict or escalator-added
|-- EDGE_CASES.md                 # standard/strict or escalator-added
|-- ARCHITECTURE_PROPOSAL.md      # standard/strict or escalator-added
|-- FLOW_DIAGRAM.md               # standard/strict or escalator-added
|-- STATE.json                    # runtime checkpoint
|-- EVENTS.jsonl                  # append-only event log
|-- consults/                     # meet notes
`-- feedback/
    |-- ARCH_FEEDBACK.md
    |-- REVIEW_FAILURES.md
    |-- IMPL_QUESTIONS.md
    |-- DESIGN_QUESTIONS.md
    |-- TEST_FAILURES.md
    `-- HUMAN_QUESTIONS.md
```

Feedback files are control-plane signals. File present means issue open. File
deleted means resolved. The FSM must not move forward while any known feedback
file exists.

---

## Python CLI

The `pathly` command exposes these stable surfaces:

```bash
pathly help [feature]          # state-aware menu
pathly init <feature>          # create a lite starter plan
pathly status [feature]        # current FSM state + suggested next action
pathly doctor                  # diagnose: engine installed, plans/ accessible, STATE.json readable
pathly flow <feature>          # run the Python team-flow driver
pathly flow <feature> --fast   # run without pause points
pathly flow <feature> --entry build|test  # jump to a specific stage
```

---

## Natural Language Activation

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

## What pathly-engine Is NOT

- Not a standalone process — it runs inside the AI coding tool or as a terminal CLI
- Not a replacement for Claude Code / Codex / Copilot — it extends them
- Not a conversation manager — context isolation is handled by Agent() (Claude Code) or equivalent
- Not the installer — installing agent files into host tools is pathly-adapters' job
