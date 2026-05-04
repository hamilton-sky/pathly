# Claude Agents Framework

A role-based agent system for Claude Code where **files are the protocol**,
**behavioral contracts** define how each agent thinks, and **feedback loops**
route issues back to the right agent automatically.

## What this is

12 specialized agents + lifecycle skills that give Claude Code a structured
development pipeline: brainstorm → plan → implement → review → test → retro → learn.

Unlike conversation-based workflows, state lives on disk. Agents hand off via
files, and the orchestrator behaves as a deterministic filesystem state
machine. An open feedback file blocks the pipeline. A deleted file means
resolved.

Claude Agents Framework is primarily a **Claude Code plugin**. It also includes
a small Python orchestrator module used by the `team-flow` driver and tests. The
Python package metadata exists to make local development and CI repeatable; end
users normally install and use the Claude plugin, not a standalone Python app.

**New in this version:**
- **Rigor escalator** — starts at `lite` (4 files), offers targeted additions based on what planning reveals
- **`/debug <symptom>`** — dedicated bug pipeline: discoverer traces, tester verifies before and after fix
- **`/explore <question>`** — investigation mode: answer questions about the codebase without building
- **`/help --doctor`** — diagnoses stuck FSM, orphan feedback files, stale state; offers one action per issue
- **`[AUTO_FIX]` in reviewer** — trivial findings (unused import, missing newline) applied in batch, no human turn
- **Cost meter** — `RETRO.md` shows per-agent token + cost breakdown from `EVENTS.jsonl`
- **Inline quick queries** — builder can ask atomic questions (≤ 2 tool calls) without creating feedback files
- **TTL on feedback files** — frontmatter tracks creation event; `/verify-state` detects orphans and expired files
- **Startup integrity check** — every `/team-flow` run scans for orphan/expired feedback files and FSM drift before the first agent spawns; fast mode auto-resolves safe issues, stops on real ones

---

## Quick install

```bash
# macOS / Linux
git clone https://github.com/hamilton/claude-agents-framework
cd claude-agents-framework
bash install.sh

# Optional: register the auto-classification hook
bash scripts/setup-hook.sh
```

```powershell
# Windows (PowerShell)
git clone https://github.com/hamilton/claude-agents-framework
cd claude-agents-framework
.\install.ps1

# Optional: register the auto-classification hook
.\scripts\setup-hook.ps1
```

**To uninstall:**
```bash
bash install.sh --uninstall           # macOS / Linux
.\install.ps1 -Uninstall              # Windows
```

Then open any project in Claude Code and run:
```
/go <what you want>
```

Director reads the current project state, chooses the lightest safe workflow,
and routes into the right skill:
```
/go add user authentication with Google OAuth
```

No need to know the pipeline commands to get started.

**If you already know the pipeline**, use skills directly:
```
/go                                       ← prompts "What do you want?" then routes
/go I want to add user authentication     ← skip the prompt, routes immediately
/team-flow <feature-name>                 ← direct pipeline entry
/team-flow <feature-name> build           ← resume implementation
/team-flow <feature-name> test            ← run test stage
/review                                   ← review the current diff
```

`/team-flow` opens with a path selector:
```
[1] Quick storm    — architect explores the idea first
[2] Skip discovery — you know what to build, go straight to planning
[3] Import PRD     — you have a requirements file (from BMAD or hand-written)
```

Pick your path, type the number, and the pipeline runs from there.
The other skills (`/storm`, `/plan`, `/prd-import`, `/bmad-import`) exist for manual control
when you need to jump into the middle of a pipeline.

Choose process rigor with `lite`, `standard`, or `strict`:
```
/team-flow small-ui-copy lite       ← 4-file plan, lighter gates
/team-flow payment-flow standard    ← full 8-file pipeline
/team-flow auth-migration strict    ← mandatory approvals, audit logs, full gates
```

Default is `lite` — the **rigor escalator** detects signals during planning
(cross-layer deps, high-risk keywords, many conversations) and offers specific
additional plan files before the first build. In `fast` mode it applies all
recommended files automatically.

`fast` controls pauses. Rigor controls process depth. `strict` rejects `fast`
because strict mode requires human approval gates.

---

## Supported versions

- Claude Code plugin system is the primary runtime.
- Python 3.11+ is required for local development and tests.
- CI runs the test suite on Python 3.11, 3.12, and 3.13.
- The plugin is designed for project-local use through Claude Code. The Python
  metadata is for development and CI, not a separate production service.

---

## Development and tests

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest -q
```

The test suite covers the core FSM, event log persistence, and driver-support
edge cases. End-to-end agent behavior still depends on Claude Code and should be
validated with smoke runs before release.

---

## Director, /go, and /team-flow

**Director** is the decision-making agent role. It reads the user's free-form
request, inspects project state, chooses `nano`, `lite`, `standard`, or
`strict`, and decides whether to start discovery, planning, build, test, review,
or retro.

**`/go`** is the normal user command. It activates Director:

```text
/go fix the broken checkout button
/go add password reset
/go continue the login work
/go review my current changes
```

**`/team-flow`** is the explicit pipeline command. Use it when you already know
the feature name, rigor, and entry point:

```text
/team-flow password-reset strict
/team-flow navbar-copy nano
/team-flow checkout build
```

Direct skills such as `/build`, `/review`, and `/retro` are for manual recovery
or advanced control.

---

## Docs

| Doc | What's in it |
|---|---|
| [docs/FLOW_DIAGRAM.md](docs/FLOW_DIAGRAM.md) | Full pipeline flow — Mermaid overview + ASCII lifecycle, feedback loops, agents, entry points |
| [docs/FAST_MODE_FLOW.md](docs/FAST_MODE_FLOW.md) | Fast mode flow — ASCII + Mermaid diagrams showing auto-advance vs hard stops |
| [docs/ARCHITECTURE_AGENTS.md](docs/ARCHITECTURE_AGENTS.md) | Full pipeline, agent map, file handoff protocol, quick reference |
| [docs/BUILDER_DELEGATION_PLAN.md](docs/BUILDER_DELEGATION_PLAN.md) | Two-tier sub-agent delegation design — scout (codebase) + web-researcher (external), constraints, ownership rules |
| [docs/ORCHESTRATOR_FSM.md](docs/ORCHESTRATOR_FSM.md) | Deterministic state machine model, events, recovery, guards |
| [docs/FEEDBACK_PROTOCOL.md](docs/FEEDBACK_PROTOCOL.md) | Each feedback file format with templates + escalation rules |
| [docs/SECURITY_RELIABILITY_REVIEW.md](docs/SECURITY_RELIABILITY_REVIEW.md) | Security/reliability posture, risks, mitigations, and production checklist |
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | Philosophy — why files as protocol, why feedback loops |
| [docs/MULTI_TOOL_DESIGN.md](docs/MULTI_TOOL_DESIGN.md) | Roadmap for Cursor / Windsurf / BMAD adapter layer |

---

## The 12 Agents

| Agent | Model | Role | Thinks about |
|---|---|---|---|
| `director` | Sonnet | Workflow direction | Intent, risk, rigor, entry point |
| `architect` | Opus | Technical architecture | Layers, trade-offs, dependency direction |
| `po` | Opus | Requirements advisor | Scope, assumptions, MVP, PRD validation |
| `planner` | Sonnet | Requirements | User value, stories, acceptance criteria |
| `builder` | Sonnet | Implementation | Exact scope, verify before done |
| `reviewer` | Sonnet | Adversarial review | Contract violations, never fixes |
| `tester` | Sonnet | Verification | AC coverage, reports bugs only |
| `discoverer` | Sonnet | Site tracing | Follows visible paths, captures trace |
| `quick` | Haiku | Fast lookups | 2 tool calls max |
| `orchestrator` | Haiku | FSM sequencing | Recovers state, processes events, emits one agent action |
| `scout` | Haiku | Codebase investigation | Read-only cross-file pattern lookup; advisory, no writes |
| `web-researcher` | Haiku | External research | Web search for docs, patterns, standards; cited findings only |

---

## Core Skills

| Skill | Command | What it does |
|---|---|---|
| `team-flow` | `/team-flow <feature>` | Full pipeline: discovery→plan→build×N→test→retro with rigor escalator |
| `storm` | `/storm` | Architect explores the idea with ASCII diagrams |
| `plan` | `/plan <feature> [lite|standard|strict]` | Creates `plans/<feature>/` with 4 core files + escalator-selected extras |
| `build` | `/build <feature>` | Implements the next TODO conversation |
| `review` | `/review` | Reviewer audits code; trivial findings tagged `[AUTO_FIX]` for batch apply |
| `retro` | `/retro <feature>` | Writes RETRO.md with cost summary + appends to LESSONS_CANDIDATE.md |
| `lessons` | `/lessons` | Promotes candidate lessons to LESSONS.md for planner |
| `archive` | `/archive <feature>` | Moves completed plan to `plans/.archive/` |
| `prd-import` | `/prd-import <feature> <prd.md> [lite|standard|strict]` | Translates any PRD file into plan files |
| `bmad-import` | `/bmad-import <feature> <prd.md> [lite|standard|strict]` | Translates a BMAD PRD into plan files |
| `verify-state` | `/verify-state [feature]` | Checks orphan/expired feedback files (TTL), PROGRESS drift, dead code references |
| `debug` | `/debug <symptom>` | Bug pipeline: discoverer traces → builder fixes → tester verifies before + after |
| `explore` | `/explore <question>` | Investigation mode: answer codebase questions without building anything |
| `help` | `/help [--doctor] [feature]` | State menu; `--doctor` diagnoses stuck FSM and orphan files with action suggestions |

---

## Rigor Modes

The pipeline **always creates 4 core plan files** regardless of rigor:
`USER_STORIES.md`, `IMPLEMENTATION_PLAN.md`, `PROGRESS.md`, `CONVERSATION_PROMPTS.md`

Additional files are added by the **rigor escalator** (signal-based) or by explicit choice:

| Rigor | Best for | Extra files | Gates |
|---|---|---|---|
| `lite` *(default)* | Small, low-risk changes | None beyond 4 core (escalator may add targeted extras) | Build-focused, review/test can be final-only |
| `standard` | Normal product features | `HAPPY_FLOW.md`, `EDGE_CASES.md`, `ARCHITECTURE_PROPOSAL.md`, `FLOW_DIAGRAM.md` | Review after every conversation, test, retro |
| `strict` | Auth, payments, migrations, compliance | All 8 files + required `STATE.json` + `EVENTS.jsonl` | Mandatory approvals, review, test mapping, audit trail |

**Rigor escalator:** after planning, the orchestrator checks for signals (cross-layer
dependencies, high-risk keywords, > 3 conversations, long discovery path) and offers to
add the specific extra files that are warranted — with the signal shown per file. In `fast`
mode, all recommended files are added automatically. Explicit rigor flags (`standard`,
`strict`) bypass the escalator and add the full file set.

To move a feature between rigor levels, do not delete files. Upgrade by running
`/plan <feature> standard` or `/plan <feature> strict` to add missing plan
files. Downgrade by running `/team-flow <feature> lite`; extra files remain as
references while future gates become lighter.

---

## The Feature Pipeline

```
/team-flow payment-flow

  Stage 1 — Storm      architect explores idea  →  STORM_SEED.md
       PAUSE: "Ready to plan?"
  Stage 2 — Plan       planner creates rigor-specific files → plans/payment-flow/
       PAUSE: "Review plan. go / stop"
  Stage 3 — Implement  builder + reviewer loop  →  code + PROGRESS.md
       ├─ builder hits [REQ] blocker → IMPL_QUESTIONS.md → planner
       ├─ builder hits [ARCH] blocker → DESIGN_QUESTIONS.md → architect
       ├─ builder hits [UNSURE] blocker → both files → correct owner discards
       ├─ reviewer finds violation → REVIEW_FAILURES.md → builder
       │    └─ builder fixes nothing (zero git diff) → HUMAN_QUESTIONS.md [STALL]
       └─ reviewer passes → advance
       PAUSE: "Commit. continue / stop"
  Stage 4 — Test       tester maps ACs to tests → TEST_FAILURES.md → builder
  Stage 5 — Retro      quick writes RETRO.md
```

Add `fast` to skip pause points:
```
/team-flow payment-flow fast
```

Jump into the middle of a pipeline:
```
/team-flow payment-flow build   ← plan exists, start implementing
/team-flow payment-flow test    ← all built, run tests only
/team-flow payment-flow plan    ← skip discovery, start planning
/team-flow payment-flow fast    ← no pauses, run to completion
/team-flow payment-flow build fast  ← resume build with no pauses
```

Each flag runs a health check first — missing plan files or incomplete
conversations are caught before any agent spawns.

---

## Feedback File Protocol

6 files in `plans/<feature>/feedback/`. **File exists = issue open. Deleted = resolved.**

Every feedback file carries a YAML frontmatter block (injected by `inject_feedback_ttl.py`):
```yaml
---
created_at: 2026-05-04T08:12:00Z
created_by_event: <last-event-id>
ttl_hours: 24
---
```
`/verify-state` and `/help --doctor` use this to detect orphan files (event not in current log) and expired files (TTL elapsed) — both are safe to delete automatically.

| File | Written by | Resolved by |
|---|---|---|
| `ARCH_FEEDBACK.md` | reviewer | architect |
| `REVIEW_FAILURES.md` | reviewer | builder (`[AUTO_FIX]` patches applied in batch; regular violations handled normally) |
| `IMPL_QUESTIONS.md` | builder `[REQ]` | planner |
| `DESIGN_QUESTIONS.md` | builder `[ARCH]` | architect |
| `TEST_FAILURES.md` | tester | builder |
| `HUMAN_QUESTIONS.md` | any agent / `[STALL]` / `[RIGOR]` | user *(blocks pipeline)* |

`ARCH_FEEDBACK.md` is blocking — no building until architect resolves it.
The full transition model is defined in [docs/ORCHESTRATOR_FSM.md](docs/ORCHESTRATOR_FSM.md).

---

## PRD Import

If you have a hand-written spec, AI-generated PRD, or any structured requirements file:

```
/prd-import hotel-search docs/hotel-search-prd.md standard
```

If the PRD came from BMAD, use the BMAD-specific importer:

```
/bmad-import hotel-search docs/hotel-search-prd.md standard
```

This reads the PRD and generates plan files for the selected rigor — translating:
- Acceptance Criteria → verify commands
- Edge Cases → workflow conversation prompts
- Out of Scope → Do NOT lists in every builder prompt

Then continue normally with `/build hotel-search` or `/team-flow hotel-search`.

**No PRD?** Use `/team-flow` — it asks you to choose: quick storm, skip discovery, or import a PRD.

---

## What gets installed

```
~/.claude/
├── agents/                    ← 9 behavioral contracts (.md files)
├── skills/                    ← lifecycle skills (go, team-flow, build, plan, ...)
└── plugins/claude-agents-framework/
    ├── hooks/
    │   ├── classify_feedback.py    ← tags IMPL_QUESTIONS.md on write, splits [ARCH] questions
    │   └── inject_feedback_ttl.py  ← injects TTL frontmatter into every feedback file on write
    └── templates/plan/             ← plan file templates used by /plan, /prd-import, /bmad-import
        └── *.template.md
```

Run `bash scripts/setup-hook.sh` (or `.\scripts\setup-hook.ps1`) after install to register the hooks in `settings.json`.

---

## Philosophy

1. **Agent = behavioral contract, not persona.** The role defines HOW the agent thinks, not a character it plays.
2. **Files are the contract between roles.** No agent calls another directly. State lives on disk and is recovered by the orchestrator FSM.
3. **Human checkpoints are the point.** The pipeline pauses at every stage transition.
4. **Feedback loops, not a linear chain.** Wrong problem routes to the right role automatically.

See [docs/ARCHITECTURE_AGENTS.md](docs/ARCHITECTURE_AGENTS.md) for the full architecture.
