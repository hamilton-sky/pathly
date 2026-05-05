# Pathly

Tell it what you want. Pathly chooses the path.

Pathly is a guided agent workflow system for real software development. It helps
AI coding tools plan, build, review, debug, test, and learn from changes without
making you manage the process by hand.

Start with plain English:

```text
/pathly add password reset
/pathly fix the checkout bug
/pathly review my current changes
/pathly continue the current feature
```

/path is the short alias for /pathly in slash-command tools.

Not sure what to do next?

```text
/pathly help
```

Something stuck?

```text
/pathly doctor
```

Have a question about the codebase?

```text
/pathly explore how does checkout state flow through the app?
```

Have a bug?

```text
/pathly debug checkout button does nothing
```

## What This Is

A role-based agent system where **files are the protocol**,
**behavioral contracts** define how each agent thinks, and **feedback loops**
route issues back to the right role automatically.

11 specialized agents + lifecycle skills give AI coding tools a structured
development pipeline: brainstorm -> plan -> implement -> review -> test ->
retro -> learn.

Unlike conversation-based workflows, state lives on disk. Agents hand off via
files, and the orchestrator behaves as a deterministic filesystem state
machine. An open feedback file blocks the pipeline. A deleted file means
resolved.

Pathly ships as an installable Python tool with adapter layers for Claude Code
and Codex. The `pathly` CLI owns the stable local contract: install it once,
run it from any project folder, and let the Claude/Codex adapters expose the
same workflow in their native UI.

**New in this version:**
- **Rigor escalator** — starts at `lite` (4 files), offers targeted additions based on what planning reveals
- **`/pathly debug <symptom>`** — dedicated bug pipeline: scout traces, tester verifies before and after fix
- **`/pathly explore <question>`** — investigation mode: answer questions about the codebase without building
- **`/pathly doctor`** — diagnoses stuck FSM, orphan feedback files, stale state; offers one action per issue
- **`[AUTO_FIX]` in reviewer** — trivial findings (unused import, missing newline) applied in batch, no human turn
- **Cost meter** — `RETRO.md` shows per-agent token + cost breakdown from `EVENTS.jsonl`
- **Inline quick queries** — builder can ask atomic questions (≤ 2 tool calls) without creating feedback files
- **TTL on feedback files** — frontmatter tracks creation event; `/pathly verify-state` detects orphans and expired files
- **Startup integrity check** — every `/pathly flow` run scans for orphan/expired feedback files and FSM drift before the first agent spawns; fast mode auto-resolves safe issues, stops on real ones

---

## Install

### Claude Code

```bash
# macOS / Linux
git clone https://github.com/hamilton-sky/pathly
cd pathly
bash install.sh

# Optional: register the auto-classification hook
bash scripts/setup-hook.sh
```

```powershell
# Windows (PowerShell)
git clone https://github.com/hamilton-sky/pathly
cd pathly
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
/pathly <what you want>
```

Director reads the current project state, chooses the lightest safe workflow,
and routes into the right skill. You do not need to know the pipeline commands
to get started.

### Codex

Pathly includes a Codex plugin manifest at `.codex-plugin/plugin.json`.
Current Codex builds load local plugins through a marketplace root. Create a
small local marketplace that points to your Pathly checkout, then add that
marketplace to Codex.

Example Windows setup:

```powershell
git clone https://github.com/hamilton-sky/pathly
cd pathly
python -m pip install -e .

$market = "C:\tmp\pathly-marketplace"
New-Item -ItemType Directory -Path "$market\.agents\plugins" -Force
New-Item -ItemType Directory -Path "$market\plugins" -Force
New-Item -ItemType Junction -Path "$market\plugins\pathly" -Target (Get-Location)
@'
{
  "name": "pathly-local",
  "interface": {
    "displayName": "Pathly Local"
  },
  "plugins": [
    {
      "name": "pathly",
      "source": {
        "source": "local",
        "path": "./plugins/pathly"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
'@ | Set-Content "$market\.agents\plugins\marketplace.json"

codex plugin marketplace add $market
```

For local marketplaces, `codex plugin marketplace upgrade pathly-local` is not
needed; upgrade is for Git-backed marketplaces.

Then open any project in Codex and invoke Pathly with natural language:

```text
Use Pathly help
Use Pathly doctor on this project
Use Pathly to add user authentication with Google OAuth
Use Pathly to debug checkout button does nothing
Use Pathly to explore how checkout works
```

Do not expect `/pathly` to work in current Codex builds; Codex reserves slash
commands for its own UI. Codex support currently exposes the skill workflow
layer through plugin skills and the `pathly` CLI fallback. Claude-style custom
agent files remain available as role contracts, but full multi-tool adapter
packaging is tracked in [docs/MULTI_TOOL_DESIGN.md](docs/MULTI_TOOL_DESIGN.md).

### Pathly CLI

Install Pathly as an editable package while developing or from a cloned repo on
a new machine:

```bash
python -m pip install -e ".[dev]"
pathly --help
```

Run Pathly from any project folder:

```bash
pathly init checkout-flow
pathly run checkout-flow --entry build
pathly doctor
```

You can also point Pathly at another project explicitly:

```bash
pathly --project-dir C:\Users\Yafit\pathly-test init demo
pathly --project-dir C:\Users\Yafit\pathly-test run demo --entry build
```

Adapter install helpers show the commands for each host:

```bash
pathly install codex
pathly install claude
```

### Developer Install

Use the development extra when changing Pathly itself or running tests:

```bash
python -m pip install -e ".[dev]"
pytest -q
```

**If you already know the pipeline**, use skills directly:
```
/pathly                                       ← prompts "What do you want?" then routes
/pathly I want to add user authentication     ← skip the prompt, routes immediately
/pathly flow <feature-name>                 ← direct pipeline entry
/pathly flow <feature-name> build           ← resume implementation
/pathly flow <feature-name> test            ← run test stage
/pathly review                                   ← review the current diff
```

`/pathly flow` opens with a path selector:
```
[1] Quick storm    — architect explores the idea first
[2] Skip discovery — you know what to build, go straight to planning
[3] Import PRD     — you have a requirements file (from BMAD or hand-written)
```

Pick your path, type the number, and the pipeline runs from there.
The other skills (`/pathly storm`, `/pathly plan`, `/pathly prd-import`, `/pathly bmad-import`) exist for manual control
when you need to jump into the middle of a pipeline.

Choose process rigor with `lite`, `standard`, or `strict`:
```
/pathly flow small-ui-copy lite       ← 4-file plan, lighter gates
/pathly flow payment-flow standard    ← full 8-file pipeline
/pathly flow auth-migration strict    ← mandatory approvals, audit logs, full gates
```

Default is `lite` — the **rigor escalator** detects signals during planning
(cross-layer deps, high-risk keywords, many conversations) and offers specific
additional plan files before the first build. In `fast` mode it applies all
recommended files automatically.

`fast` controls pauses. Rigor controls process depth. `strict` rejects `fast`
because strict mode requires human approval gates.

---

## Supported Versions

- Claude Code plugin support is available today.
- Codex plugin support is available through `.codex-plugin/plugin.json`.
- Cursor, Windsurf, BMAD, and generic prompt adapters are planned in
  [docs/MULTI_TOOL_DESIGN.md](docs/MULTI_TOOL_DESIGN.md).
- Python 3.11+ is required for local development and tests.
- CI runs the test suite on Python 3.11, 3.12, and 3.13.
- The Python package exposes the `pathly` CLI used by local development,
  smoke tests, and adapter wrappers.

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

## Everyday Commands

**Director** is the decision-making agent role. It reads the user's free-form
request, inspects project state, chooses `nano`, `lite`, `standard`, or
`strict`, and decides whether to start discovery, planning, build, test, review,
or retro.

**`/pathly`** is the normal user command. It activates Director:

```text
/pathly fix the broken checkout button
/pathly add password reset
/pathly continue the login work
/pathly review my current changes
```

**`/pathly flow`** is the explicit pipeline command. Use it when you already know
the feature name, rigor, and entry point:

```text
/pathly flow password-reset strict
/pathly flow navbar-copy nano
/pathly flow checkout build
```

Direct skills such as `/pathly continue`, `/pathly review`, and `/pathly retro` are for manual recovery
or advanced control.

**`/pathly help`** is the state-aware menu. Use it when you are unsure what to do next.
`/pathly doctor` runs diagnostics for stuck state, orphan feedback files, and
pipeline drift.

**`/pathly debug`** is for known bug symptoms. It traces the repro, confirms the bug
before the fix, applies the fix, and verifies after.

**`/pathly explore`** is for codebase questions. It investigates and writes findings
without building anything.

---

## Docs

| Doc | What's in it |
|---|---|
| [docs/FLOW_DIAGRAM.md](docs/FLOW_DIAGRAM.md) | Full pipeline flow — Mermaid overview + ASCII lifecycle, feedback loops, agents, entry points |
| [docs/FAST_MODE_FLOW.md](docs/FAST_MODE_FLOW.md) | Fast mode flow — ASCII + Mermaid diagrams showing auto-advance vs hard stops |
| [docs/ARCHITECTURE_AGENTS.md](docs/ARCHITECTURE_AGENTS.md) | Full pipeline, agent map, file handoff protocol, quick reference |
| [docs/ORCHESTRATOR_FSM.md](docs/ORCHESTRATOR_FSM.md) | Deterministic state machine model, events, recovery, guards |
| [docs/FEEDBACK_PROTOCOL.md](docs/FEEDBACK_PROTOCOL.md) | Each feedback file format with templates + escalation rules |
| [docs/SECURITY_RELIABILITY_REVIEW.md](docs/SECURITY_RELIABILITY_REVIEW.md) | Security/reliability posture, risks, mitigations, and production checklist |
| [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md) | Release criteria, install checks, naming tasks, and adapter-readiness gaps |
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | Philosophy — why files as protocol, why feedback loops |
| [docs/MULTI_TOOL_DESIGN.md](docs/MULTI_TOOL_DESIGN.md) | Roadmap for Cursor / Windsurf / BMAD adapter layer |

---

## The 11 Agents

| Agent | Model | Tools | Enforced boundary |
|---|---|---|---|
| `director` | Sonnet | Read, Glob, Grep, Agent | Reads and routes; does not write |
| `architect` | Opus | Read, Glob, Grep, Write, Edit, Agent | Writes/edits design docs; no Bash |
| `po` | Opus | Read, Write | Reads PRDs and writes `PO_NOTES.md` only |
| `planner` | Sonnet | Read, Glob, Grep, Write, Edit, Agent | Writes/edits plans; no Bash or direct web tools |
| `builder` | Sonnet | Read, Glob, Grep, Edit, Write, Bash, Agent, TodoWrite | Full implementation access; no web tools |
| `reviewer` | Sonnet | Read, Glob, Grep, Write, Agent | Writes feedback and spawns scouts; no source edits or Bash |
| `tester` | Sonnet | Read, Glob, Grep, Bash, Write, Agent | Runs tests and writes failures; no source edits |
| `quick` | Haiku | Read, Glob, Grep | Local lookup only; no writes or spawning |
| `orchestrator` | Haiku | Read, Glob, Grep, Write, Edit, Bash, Agent | Manages FSM state and spawns agents; no web |
| `scout` | Haiku | Read, Glob, Grep | Read-only local investigation; no writes, spawn, or web |
| `web-researcher` | Haiku | WebSearch, WebFetch | Web-only research; cannot touch local files |

---

## Sub-agent delegation

Builder (and a few other agents) can spawn lightweight read-only sub-agents
before touching any code. Sub-agents collect context in parallel; they never
edit files, never resolve feedback files, and cannot spawn further agents.

| Tier | Agent | Who can use it | Budget |
|---|---|---|---|
| 1 | `quick` | builder only (inline) | ≤ 2 tool calls |
| 2 | `scout` | builder, architect, reviewer, tester | 5–15 tool calls |
| 3 | `web-researcher` | architect, planner | web search, cited findings |

**Cap:** 4 sub-agents per conversation (shared across all tiers).

**Builder flow:**
1. Identify unknowns that can be answered independently.
2. Spawn up to 3 scouts (or 1 quick + scouts) in parallel.
3. Collect findings, form an implementation approach.
4. Edit files as builder. Sub-agent output is advisory only.

**Inline quick query** — for a single atomic lookup (e.g. "what is the import
path for X?"), builder can call `quick` directly with ≤ 2 tool calls and no
file writes. No feedback file created, no FSM event emitted.

See [docs/ARCHITECTURE_AGENTS.md](docs/ARCHITECTURE_AGENTS.md) for the full
tier rules, per-agent sub-agent lists, and ownership guarantees.

---

## Core Skills

| Skill | Command | What it does |
|---|---|---|
| `team-flow` | `/pathly flow <feature>` | Full pipeline: discovery→plan→build×N→test→retro with rigor escalator |
| `storm` | `/pathly storm` | Architect explores the idea with ASCII diagrams |
| `plan` | `/pathly plan <feature> [lite|standard|strict]` | Creates `plans/<feature>/` with 4 core files + escalator-selected extras |
| `build` | `/pathly continue <feature>` | Implements the next TODO conversation |
| `review` | `/pathly review` | Reviewer audits code; trivial findings tagged `[AUTO_FIX]` for batch apply |
| `retro` | `/pathly retro <feature>` | Writes RETRO.md with cost summary + appends to LESSONS_CANDIDATE.md |
| `lessons` | `/pathly lessons` | Promotes candidate lessons to LESSONS.md for planner |
| `archive` | `/pathly archive <feature>` | Moves completed plan to `plans/.archive/` |
| `prd-import` | `/pathly prd-import <feature> <prd.md> [lite|standard|strict]` | Translates any PRD file into plan files |
| `bmad-import` | `/pathly bmad-import <feature> <prd.md> [lite|standard|strict]` | Translates a BMAD PRD into plan files |
| `verify-state` | `/pathly verify-state [feature]` | Checks orphan/expired feedback files (TTL), PROGRESS drift, dead code references |
| `debug` | `/pathly debug <symptom>` | Bug pipeline: scout traces → builder fixes → tester verifies before + after |
| `explore` | `/pathly explore <question>` | Investigation mode: answer codebase questions without building anything |
| `help` | `/pathly help [--doctor] [feature]` | State menu; `--doctor` diagnoses stuck FSM and orphan files with action suggestions |

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
`/pathly plan <feature> standard` or `/pathly plan <feature> strict` to add missing plan
files. Downgrade by running `/pathly flow <feature> lite`; extra files remain as
references while future gates become lighter.

---

## The Feature Pipeline

```
/pathly flow payment-flow

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
  Stage 5 — Retro      quick summarizes; retro skill writes RETRO.md
```

Add `fast` to skip pause points:
```
/pathly flow payment-flow fast
```

Jump into the middle of a pipeline:
```
/pathly flow payment-flow build   ← plan exists, start implementing
/pathly flow payment-flow test    ← all built, run tests only
/pathly flow payment-flow plan    ← skip discovery, start planning
/pathly flow payment-flow fast    ← no pauses, run to completion
/pathly flow payment-flow build fast  ← resume build with no pauses
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
`/pathly verify-state` and `/pathly doctor` use this to detect orphan files (event not in current log) and expired files (TTL elapsed) — both are safe to delete automatically.

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
/pathly prd-import hotel-search docs/hotel-search-prd.md standard
```

If the PRD came from BMAD, use the BMAD-specific importer:

```
/pathly bmad-import hotel-search docs/hotel-search-prd.md standard
```

This reads the PRD and generates plan files for the selected rigor — translating:
- Acceptance Criteria → verify commands
- Edge Cases → workflow conversation prompts
- Out of Scope → Do NOT lists in every builder prompt

Then continue normally with `/pathly continue hotel-search` or `/pathly flow hotel-search`.

**No PRD?** Use `/pathly flow` — it asks you to choose: quick storm, skip discovery, or import a PRD.

---

## What gets installed

```
~/.claude/
├── agents/                    ← 11 behavioral contracts (.md files)
├── skills/                    ← installed Claude Code lifecycle skills
└── plugins/pathly/
    ├── hooks/
    │   ├── classify_feedback.py    ← tags IMPL_QUESTIONS.md on write, splits [ARCH] questions
    │   └── inject_feedback_ttl.py  ← injects TTL frontmatter into every feedback file on write
    └── templates/pathly plan/             ← plan file templates used by /pathly plan, /pathly prd-import, /pathly bmad-import
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

