# Pathly Engine Architecture

Pathly-engine is the FSM runtime for the Pathly agent workflow system. It owns
deterministic workflow state management, subprocess runners, and the `pathly`
CLI entry point.

## Package Layout

```text
pathly-engine/                   ← pip package: pathly-engine (CLI: pathly)
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

## Agent Roles

Pathly defines eleven role contracts in `core/agents/` (in pathly-adapters). The
engine FSM references these roles by name.

| Agent | Responsibility | Boundary |
|---|---|---|
| `director` | Classify intent and route to the lightest safe workflow. | Reads and routes; no source edits. |
| `po` | Clarify product intent, user value, MVP scope, and success criteria. | Optional/on-demand; writes product notes only. |
| `architect` | Resolve design, layer, contract, migration, and rollback questions. | Design docs and architecture feedback, not implementation. |
| `planner` | Write stories, acceptance criteria, task order, and plan files. | Plan files only; consults PO or architect when uncertainty is real. |
| `builder` | Implement the next scoped conversation and verify it. | Source edits allowed; does not silently change scope or architecture. |
| `reviewer` | Find contract, behavior, and diff-quality problems. | Writes findings; does not fix source. |
| `tester` | Map acceptance criteria to verification and report failures. | Runs/verifies tests; does not fix source. |
| `orchestrator` | Recover state and emit the next action. | FSM and routing only. |
| `quick` | Atomic lookup or short summary. | Read-only, small budget. |
| `scout` | Read-only codebase investigation. | No writes or workflow decisions. |
| `web-researcher` | External research with citations. | Web-only context; no local edits. |

## Agent Hierarchy

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

**quick vs scout:**
- `quick` — 1-2 tool calls, single factual lookup, inline answer, no report format
- `scout` — 5-15 tool calls, cross-file investigation, structured Findings/Recommendation/Ambiguities report

## Consultation Policy

The default pipeline stays lean:

- `po` has a dedicated `/pathly po [feature]` skill — structured Q&A, writes `PO_NOTES.md`. Shown as step 0 in the journey map.
- `architect` is on-demand unless rigor or risk requires design review.
- Builder-side consultation must be a bounded question with a concrete output.
- `meet` is a separate read-only consultation workflow with **context-aware menus** — the roles offered change based on the current FSM state (7 different menus: storming, planning, building, review-open, arch-open, testing, done).
- `director`, `orchestrator`, `builder`, `quick`, and `scout` are **not** valid `meet` targets — they are pipeline-internal roles.
- `po` is offered in `meet` during storming, planning, and building states.
- `web-researcher` is offered in `meet` only when the user's question explicitly needs external sources.

`meet` writes notes under `plans/<feature>/consults/`. Promotion to planner or
architect updates is a follow-up action, not something the consulted role does
directly.

## Workflow Files

`pathly init <feature>` and the planning workflows create the four core files:

```text
plans/<feature>/
|-- USER_STORIES.md
|-- IMPLEMENTATION_PLAN.md
|-- PROGRESS.md
`-- CONVERSATION_PROMPTS.md
```

Standard, strict, or escalator-selected planning adds:

```text
HAPPY_FLOW.md
EDGE_CASES.md
ARCHITECTURE_PROPOSAL.md
FLOW_DIAGRAM.md
```

Runtime workflows also create:

```text
STATE.json
EVENTS.jsonl
feedback/
consults/
RETRO.md
LESSONS_CANDIDATE.md
```

## Feedback Protocol

Known feedback files live under `plans/<feature>/feedback/`.

| File | Owner to resolve |
|---|---|
| `ARCH_FEEDBACK.md` | architect |
| `DESIGN_QUESTIONS.md` | architect |
| `IMPL_QUESTIONS.md` | planner |
| `REVIEW_FAILURES.md` | builder |
| `TEST_FAILURES.md` | builder |
| `HUMAN_QUESTIONS.md` | user |

File present means issue open. File deleted means resolved.

## Rigor Modes

| Rigor | Use for | Planning surface |
|---|---|---|
| `nano` | Tiny low-risk changes | Minimal route; no full plan required by the core prompt. |
| `lite` | Default small-to-normal work | Four core plan files, with escalator additions when needed. |
| `standard` | Normal product features | All eight plan files and normal review/test gates. |
| `strict` | Auth, payments, migrations, compliance | All eight files plus audit state and explicit approvals. |

Fast mode controls pauses. Rigor controls process depth. `strict` must not
auto-advance through human approval gates.

## FSM Command Map

### Claude Code — FSM command set

```text
/pathly start               ← welcome screen + full journey map
/pathly po [feature]        ← Product Owner session (step 0)
/pathly storm [topic]       ← brainstorm with architect
/pathly go [intent]         ← director routes free-form intent
/pathly build               ← implement next conversation
/pathly pause               ← save state and exit
/pathly meet [feature]      ← context-aware role consultation
/pathly end                 ← wrap up + offer retro
/pathly help [feature]      ← state-aware menu / --doctor for diagnostics
/pathly debug <symptom>     ← bug pipeline
/pathly explore <question>  ← read-only codebase Q&A
/pathly verify [feature]    ← check stale feedback / FSM drift
```

### CLI (pathly-engine)

```text
pathly help [feature]
pathly init <feature>
pathly flow <feature> [--entry discovery|build|test] [--fast]
pathly status [feature]
pathly doctor
```

## How the Runtime Flow Works

```
User types: /team-flow my-feature
        │
        ▼
Tool reads: ~/.claude/skills/team-flow/SKILL.md
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

Each spawned agent gets a fresh context window — only the task prompt and its
behavior contract are in context. The orchestrator context stays small (state +
results only).

## STATE.json Layout

`STATE.json` is written by `team_flow/manager.py` and the orchestrator agent.
It is a checkpoint, not the source of truth — disk recovery wins if `STATE.json`
disagrees with feedback files or `PROGRESS.md`.

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

See `docs/ORCHESTRATOR_FSM.md` for the full state machine specification.
