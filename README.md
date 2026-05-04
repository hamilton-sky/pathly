# Claude Agents Framework

A role-based agent system for Claude Code where **files are the protocol**,
**behavioral contracts** define how each agent thinks, and **feedback loops**
route issues back to the right agent automatically.

## What this is

8 specialized agents + lifecycle skills that give Claude Code a structured
development pipeline: brainstorm → plan → implement → review → test → retro → learn.

Unlike conversation-based workflows, state lives on disk. Agents hand off via
files, and the orchestrator behaves as a deterministic filesystem state
machine. An open feedback file blocks the pipeline. A deleted file means
resolved.

---

## Quick install

**Via pip (recommended):**
```bash
pip install claude-agents-framework
claude-agents install
```

For the auto-classification hook (optional but recommended):
```bash
pip install "claude-agents-framework[hook]"
claude-agents install
```

**Via git clone:**
```bash
# Linux / macOS
git clone https://github.com/hamilton-sky/claude-agents-framework
cd claude-agents-framework
chmod +x install.sh && ./install.sh
```

```powershell
# Windows (PowerShell)
git clone https://github.com/hamilton-sky/claude-agents-framework
cd claude-agents-framework
.\install.ps1
```

Then open any project in Claude Code and run:
```
/help
```

Claude detects the current project state and shows a numbered menu. Pick `[1]` and describe what you want in plain English:
```
What do you want to build?
> I want to add user authentication with Google OAuth
```

Claude routes you to the right skill automatically and confirms before running. No need to know any other commands to get started.

**If you already know the pipeline**, use skills directly:
```
/go                                       ← prompts "What do you want?" then routes
/go I want to add user authentication     ← skip the prompt, routes immediately
/team-flow <feature-name>                 ← direct pipeline entry
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
/team-flow payment-flow standard    ← default full pipeline
/team-flow auth-migration strict    ← mandatory approvals, audit logs, full gates
```

`fast` controls pauses. Rigor controls process depth. `strict` rejects `fast`
because strict mode requires human approval gates.

---

## Docs

| Doc | What's in it |
|---|---|
| [docs/FLOW_DIAGRAM.md](docs/FLOW_DIAGRAM.md) | Full pipeline flow — Mermaid overview + ASCII lifecycle, feedback loops, agents, entry points |
| [docs/FAST_MODE_FLOW.md](docs/FAST_MODE_FLOW.md) | Fast mode flow — ASCII + Mermaid diagrams showing auto-advance vs hard stops |
| [docs/ARCHITECTURE_AGENTS.md](docs/ARCHITECTURE_AGENTS.md) | Full pipeline, agent map, file handoff protocol, quick reference |
| [docs/ORCHESTRATOR_FSM.md](docs/ORCHESTRATOR_FSM.md) | Deterministic state machine model, events, recovery, guards |
| [docs/FEEDBACK_PROTOCOL.md](docs/FEEDBACK_PROTOCOL.md) | Each feedback file format with templates + escalation rules |
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | Philosophy — why files as protocol, why feedback loops |
| [docs/MULTI_TOOL_DESIGN.md](docs/MULTI_TOOL_DESIGN.md) | Roadmap for Cursor / Windsurf / BMAD adapter layer |

---

## The 8 Agents

| Agent | Model | Role | Thinks about |
|---|---|---|---|
| `architect` | Opus | Technical architecture | Layers, trade-offs, dependency direction |
| `planner` | Sonnet | Requirements | User value, stories, acceptance criteria |
| `builder` | Sonnet | Implementation | Exact scope, verify before done |
| `reviewer` | Sonnet | Adversarial review | Contract violations, never fixes |
| `tester` | Sonnet | Verification | AC coverage, reports bugs only |
| `discoverer` | Sonnet | Site tracing | Follows visible paths, captures trace |
| `quick` | Haiku | Fast lookups | 2 tool calls max |
| `orchestrator` | Haiku | FSM sequencing | Recovers state, processes events, emits one agent action |

---

## Core Skills

| Skill | Command | What it does |
|---|---|---|
| `team-flow` | `/team-flow <feature>` | Full pipeline: discovery→plan→build×N→test→retro |
| `storm` | `/storm` | Architect explores the idea with ASCII diagrams |
| `plan` | `/plan <feature> [lite|standard|strict]` | Creates `plans/<feature>/` with 4 or 8 files depending on rigor |
| `build` | `/build <feature>` | Implements the next TODO conversation |
| `review` | `/review` | Reviewer audits code against rules |
| `retro` | `/retro <feature>` | Writes RETRO.md + appends to LESSONS_CANDIDATE.md |
| `lessons` | `/lessons` | Promotes candidate lessons to LESSONS.md for planner |
| `archive` | `/archive <feature>` | Moves completed plan to `plans/.archive/` |
| `prd-import` | `/prd-import <feature> <prd.md> [lite|standard|strict]` | Translates any PRD file into plan files |
| `bmad-import` | `/bmad-import <feature> <prd.md> [lite|standard|strict]` | Translates a BMAD PRD into plan files |
| `verify-state` | `/verify-state [feature]` | Checks stale feedback files, PROGRESS drift, dead code references |

---

## Rigor Modes

| Rigor | Best for | Plan files | Gates |
|---|---|---|---|
| `lite` | Small, low-risk changes | 4 files: stories, implementation plan, progress, conversation prompts | Build-focused, review/test can be final-only |
| `standard` | Normal product features | Current 8-file plan | Review after every conversation, test, retro |
| `strict` | Auth, payments, migrations, compliance, production-risk work | 8 files plus required FSM state/event logs | Mandatory approvals, review, test mapping, audit trail |

Default is `standard`.

To move a feature between rigor levels, do not delete files. Upgrade by running
`/plan <feature> standard` or `/plan <feature> strict` to add missing plan
sections/files. Downgrade by running `/team-flow <feature> standard` or
`/team-flow <feature> lite`; extra files remain as references while future gates
become lighter.

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

5 files in `plans/<feature>/feedback/`. **File exists = issue open. Deleted = resolved.**

| File | Written by | Resolved by |
|---|---|---|
| `ARCH_FEEDBACK.md` | reviewer | architect |
| `REVIEW_FAILURES.md` | reviewer | builder |
| `IMPL_QUESTIONS.md` | builder `[REQ]` | planner |
| `DESIGN_QUESTIONS.md` | builder `[ARCH]` | architect |
| `TEST_FAILURES.md` | tester | builder |
| `HUMAN_QUESTIONS.md` | any agent / `[STALL]` | user *(blocks pipeline)* |

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
├── agents/          ← 8 behavioral contracts (.md files)
├── skills/          ← lifecycle skills (storm, plan, build, imports, archive, ...)
│   └── */SKILL.md
├── hooks/           ← auto-classification hooks
│   └── classify_feedback.py  ← tags IMPL_QUESTIONS.md on write, splits [ARCH] questions
├── orchestrator/    ← FSM core deployed to ~/.claude/orchestrator/
│   ├── constants.py ← named constants for FSMState, Agent, FeedbackFile, Mode, Rigor
│   ├── utils.py     ← utc_now() shared timestamp helper
│   ├── state.py     ← 14-state immutable State dataclass; state_stack for nested blocks
│   ├── events.py    ← 9 event classes (COMMAND, AGENT_DONE, FILE_CREATED, …)
│   ├── reducer.py   ← pure reduce(state, event) → new_state; _AGENT_TRANSITIONS dict
│   └── eventlog.py  ← per-feature EVENTS.jsonl + STATE.json writer
└── templates/plan/  ← 8 plan file templates
    └── *.template.md
```

`settings.json` is updated automatically by the installer to register the hook.

Your existing `~/.claude/` content is backed up before install.

---

## Philosophy

1. **Agent = behavioral contract, not persona.** The role defines HOW the agent thinks, not a character it plays.
2. **Files are the contract between roles.** No agent calls another directly. State lives on disk and is recovered by the orchestrator FSM.
3. **Human checkpoints are the point.** The pipeline pauses at every stage transition.
4. **Feedback loops, not a linear chain.** Wrong problem routes to the right role automatically.

See [docs/ARCHITECTURE_AGENTS.md](docs/ARCHITECTURE_AGENTS.md) for the full architecture.
