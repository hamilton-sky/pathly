# Pathly Architecture And Agents

Pathly is a local agent workflow framework built around files, role contracts,
and a deterministic filesystem state machine.

## Repository Layers

This is a monorepo containing two pip packages.

```text
pathly-adapters/      pip package — installer + core content + adapter metadata
  core/               host-neutral agent contracts, skill logic, and plan templates
  adapters/           per-tool YAML metadata (_meta/) and plugin manifests
    claude/           Claude Code adapter (includes .claude-plugin/)
    codex/            Codex adapter (includes .codex-plugin/)
    copilot/          Copilot adapter
  install_cli/        pathly-setup command: detect → stitch → materialize

pathly-engine/        pip package — FSM runtime + CLI
  orchestrator/       pure FSM library (reducer, state, events, feedback)
  runners/            subprocess runners for Claude Code and Codex
  team_flow/          Python driver: wires orchestrator + runners for terminal use
  engine_cli/         pathly command entry point

.agents/              Codex marketplace metadata (plugins/marketplace.json)
plans/                feature plans and runtime state in a target project
docs/                 design, release, and review documentation
tests/                root-level integration tests
```

`core/` is content, not runtime code. `install_cli/` stitches `core/` content
with adapter `_meta/*.yaml` files at install time and deploys the result to the
host tool's config directory. The `pathly-engine` package exposes the `pathly`
console command for terminal-driven workflows.

## Adapter Surfaces

| Host | User surface | Source files |
|---|---|---|
| Claude Code | `/pathly ...`, `/go ...` | `pathly-adapters/adapters/claude/_meta/` |
| Codex | `Use Pathly ...` natural-language plugin skills | `pathly-adapters/adapters/codex/_meta/` |
| Copilot | Copilot-native skill invocation | `pathly-adapters/adapters/copilot/_meta/` |
| Terminal | `pathly ...` | `pathly-engine/engine_cli/` |

Current Codex builds do not expose Pathly as `/pathly`. Use natural-language
skill prompts in Codex docs.

## Agent Roles

Pathly defines eleven role contracts in `core/agents/`. Claude Code packages
host-specific wrappers in `adapters/claude-code/agents/`.

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

Runtime workflows may also create:

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

Fast mode controls pauses. Rigor controls process depth. `strict` should not
auto-advance through human approval gates.

## Command Map

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

### Codex

```text
Use Pathly help
Use Pathly flow for <feature>
Use Pathly to debug <symptom>
Use Pathly to explore <question>
Use Pathly po for <feature>
```

### CLI (pathly-engine)

```text
pathly help [feature]
pathly init <feature>
pathly flow <feature> [--entry discovery|build|test] [--fast]
```

### Install (pathly-adapters)

```text
pathly-setup          # detect tools, stitch core + adapter meta, deploy
```
