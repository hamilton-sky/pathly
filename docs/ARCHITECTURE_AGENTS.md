# Pathly Architecture And Agents

Pathly is a local agent workflow framework built around files, role contracts,
and a deterministic filesystem state machine.

## Repository Layers

```text
core/             host-neutral prompts, agent contracts, and templates
adapters/         Claude Code, Codex, and CLI packaging surfaces
.agents/          Codex marketplace metadata and direct skill mirror
pathly/           Python package, CLI, hooks, runners, and team-flow driver
orchestrator/     top-level Python FSM runtime package
plans/            feature plans and runtime state in a target project
docs/             design, release, and review documentation
tests/            automated checks for CLI, packaging, hooks, runners, FSM
```

`core/` is content, not runtime code. The Python import contract keeps
`orchestrator` as a top-level package and `pathly` as the installable package
that exposes the `pathly` console command.

## Adapter Surfaces

| Host | User surface | Source files |
|---|---|---|
| Claude Code | `/pathly ...`, `/path ...` | `adapters/claude-code/skills/` |
| Codex | `Use Pathly ...` natural-language plugin skills | `adapters/codex/skills/` |
| Direct skill discovery | `.agents/skills/<skill>/SKILL.md` | mirror of `adapters/codex/skills/` |
| Terminal | `pathly ...` | `pathly/cli/` |

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

- `po` is optional and on-demand.
- `architect` is on-demand unless rigor or risk requires design review.
- Builder-side consultation must be a bounded question with a concrete output.
- `meet` is a separate read-only consultation workflow.
- `director` is not a default `meet` target.

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

Claude Code:

```text
/pathly help
/pathly flow <feature>
/pathly debug <symptom>
/pathly explore <question>
/pathly meet [feature]
```

Codex:

```text
Use Pathly help
Use Pathly flow for <feature>
Use Pathly to debug <symptom>
Use Pathly to explore <question>
```

CLI:

```text
pathly help [feature]
pathly init <feature>
pathly flow <feature> [--entry discovery|build|test] [--fast]
pathly meet [feature] --role planner --question "..."
```
