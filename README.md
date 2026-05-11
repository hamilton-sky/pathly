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

## Release Status

Pathly is a public beta candidate, not a production-ready release. The core
architecture, CLI fallback, plugin manifests, and automated smoke tests are in
place, but broad production claims should wait until clean-machine install
checks, end-to-end agent smoke runs, hook hardening, and public walkthroughs are
complete.

Known limitations today:

- End-to-end agent behavior still needs manual smoke validation in Claude Code
  and Codex for each release.
- Cursor, Windsurf, BMAD, and generic prompt adapters are planned but not yet
  shipped.
- Hooks are optional and need additional path-validation and observability tests
  before they should be treated as hardened automation.
- Public case studies are still needed so users can judge real-world latency,
  token cost, and recovery behavior.

**New in this version:**
- **FSM-style command set** — 8 core commands (`start · storm · go · build · pause · meet · end · help`) + 4 specialized (`po · debug · explore · verify`); natural-language catch-all routes everything else via director
- **`/pathly po [feature]`** — dedicated Product Owner session: structured Q&A, writes `PO_NOTES.md`, shown as step 0 in the journey map
- **`/pathly start` journey map** — welcome screen now shows the full `po → storm → go → build → end` path upfront
- **`/pathly meet` context-aware menus** — 7 different role menus based on current FSM state; `po` offered in storming/planning/building; `builder`, `director`, `orchestrator` never shown as consult targets
- **web-researcher upgraded to Sonnet** — synthesis across multiple external sources needs reasoning capacity; Haiku remains for `quick` (local lookups) and `scout` (read-only investigation)
- **Retry budget bound to event ID** — retry key now uses `created_by_event` from feedback file frontmatter instead of conversation number; survives conversation replanning without silently resetting the counter
- **TTL default raised to 168h (1 week)** — avoids false positives when users pause for days; clock is now injectable for testing
- **15 new TTL tests** — `test_ttl.py` covers not-expired, expired, long-pause false positives, orphan detection, missing frontmatter
- **Protocol alignment test** — `tests/test_feedback_protocol.py` asserts Python `FeedbackFile` constants and Markdown docs reference the same filenames; prevents silent drift between runtime and behavioral contracts
- **Rigor escalator** — starts at `lite` (4 files), offers targeted additions based on what planning reveals
- **`/pathly debug <symptom>`** — dedicated bug pipeline: scout traces, tester verifies before and after fix
- **`/pathly explore <question>`** — investigation mode: answer questions about the codebase without building
- **`[AUTO_FIX]` in reviewer** — trivial findings (unused import, missing newline) applied in batch, no human turn
- **Cost meter** — `RETRO.md` shows per-agent token + cost breakdown from `EVENTS.jsonl`
- **Inline quick queries** — builder can ask atomic questions (≤ 2 tool calls) without creating feedback files
- **Startup integrity check** — every `/pathly flow` run scans for orphan/expired feedback files and FSM drift before the first agent spawns; fast mode auto-resolves safe issues, stops on real ones

---

## Install

### Claude Code

Public marketplace install:

```text
/plugin marketplace add hamilton-sky/pathly
/plugin install pathly@pathly
/reload-plugins
```

Then open any project in Claude Code and run:

```text
/pathly <what you want>
```

Local development install:

```bash
git clone https://github.com/hamilton-sky/pathly-adapters
cd pathly-adapters
pip install -e .
pathly-setup --apply          # installs into all detected hosts (Claude Code, Codex, Copilot)
```

```powershell
# Windows (PowerShell)
git clone https://github.com/hamilton-sky/pathly-adapters
cd pathly-adapters
pip install -e .
pathly-setup --apply          # installs into all detected hosts (Claude Code, Codex, Copilot)
```

Then open any project in Claude Code and run:
```
/pathly <what you want>
```

Director reads the current project state, chooses the lightest safe workflow,
and routes into the right skill. You do not need to know the pipeline commands
to get started.

### Codex

Public marketplace metadata is committed at `.agents/plugins/marketplace.json`.
If your Codex build supports GitHub marketplace shorthands, users can add the
public repository directly:

```powershell
codex plugin marketplace add hamilton-sky/pathly
```

For local testing or Codex builds that require an explicit path, clone the repo
and add the cloned directory:

```powershell
git clone https://github.com/hamilton-sky/pathly
codex plugin marketplace add C:\path\to\pathly
```

Restart Codex after adding or changing a marketplace, then invoke Pathly with
explicit natural language:

```text
Use Pathly help
Use Pathly doctor on this project
Use Pathly to add password reset
```

Local development install:

Pathly includes a Codex plugin manifest at `adapters/codex/.codex-plugin/plugin.json` inside the
[pathly-adapters](https://github.com/hamilton-sky/pathly-adapters) repo.
Current Codex builds load local plugins through a marketplace root. Let Pathly
create a small local marketplace that points to the Codex adapter inside your
checkout, then add that marketplace to Codex.

For one machine, this is effectively global: once Codex has the marketplace
registered, the Pathly plugin is available from any workspace on that machine.
Your friend still needs their own clone on their machine, because local
marketplaces point at local files.

Example Windows setup after cloning:

```powershell
git clone https://github.com/hamilton-sky/pathly-adapters
cd pathly-adapters
pip install -e .
pathly-setup codex --apply
codex plugin marketplace add C:\tmp\pathly-marketplace
```

Restart Codex after adding or changing the local marketplace. If you need to
repair the marketplace later, rerun `pathly-setup codex --apply`.

Manual PowerShell setup:

```powershell
$market = "C:\tmp\pathly-marketplace"
$plugin = "$market\plugins\pathly"
New-Item -ItemType Directory -Path "$market\.agents\plugins" -Force
New-Item -ItemType Directory -Path "$plugin" -Force
New-Item -ItemType Junction -Path "$plugin\.codex-plugin" -Target ".\adapters\codex\.codex-plugin"
New-Item -ItemType Junction -Path "$plugin\skills" -Target ".\adapters\codex\skills"
New-Item -ItemType Junction -Path "$plugin\core" -Target ".\pathly_data\core"
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

If a friend clones the repo, their next steps are:

```powershell
cd pathly-adapters
pip install -e .
pathly-setup codex --apply
codex plugin marketplace add C:\tmp\pathly-marketplace
```

Then restart/open Codex and check Settings -> Plugins for Pathly. The plugin
skills are global to that Codex install, not copied into each project.

Then open any project in Codex and invoke Pathly with explicit natural language:

```text
Use Pathly help
Use Pathly doctor on this project
Use Pathly to add user authentication with Google OAuth
Use Pathly to debug checkout button does nothing
Use Pathly to explore how checkout works
```

Short forms may work when Codex confidently selects the plugin:

```text
Pathly help
Pathly doctor
Pathly add user authentication with Google OAuth
Pathly debug checkout button does nothing
Pathly explore how checkout works
```

If Codex replies by inspecting the current repo instead of using Pathly, the
plugin was not selected. Retry with `Use Pathly ...`, confirm Pathly is enabled
in Settings -> Plugins, and restart Codex after changing a local marketplace
plugin.

Do not expect `/pathly` to work in current Codex builds; Codex reserves slash
commands for its own UI. Codex support currently exposes the skill workflow
layer through plugin skills and the `pathly` CLI fallback. Claude-style custom
agent files remain available as role contracts, but full multi-tool adapter
packaging is tracked in [pathly-adapters/docs/MULTI_TOOL_DESIGN.md](https://github.com/hamilton-sky/pathly-adapters/blob/master/docs/MULTI_TOOL_DESIGN.md).

Supported surfaces:

```text
Claude Code:  /pathly <request> or /path <request>
Codex:        Use Pathly <request>
CLI fallback: pathly --project-dir <project> help
```

### Pathly CLI (Engine)

Install the engine package:

```bash
pip install -e pathly-engine/
```

Check and advance state from any project folder:

```bash
pathly status                     # current FSM state + suggested next action
pathly status <feature>           # state for a named feature
pathly go "add password reset"    # record intent; prints current state and next step
pathly doctor                     # diagnose: engine installed, plans/ accessible, STATE.json readable
```

The `pathly` command does **not** spawn AI agents. It writes filesystem state that Claude Code or Codex reads and acts on.

### Copilot

Install agent files into VS Code with GitHub Copilot:

```bash
git clone https://github.com/hamilton-sky/pathly-adapters
cd pathly-adapters
pip install -e .
pathly-setup copilot --apply
```

Pathly agent files are installed as Copilot custom instructions. Invocation syntax varies by VS Code / Copilot version — check your Copilot chat settings after install. Keep Claude Code slash-command examples (`/pathly`) separate from Copilot usage; they are different surfaces.

### Token Activity Log

Track agent runs and token usage across all projects:

```bash
pathly-tokens
```

Each agent records its work to `~/.pathly/activity.jsonl` when it finishes a task. `pathly-tokens` prints a grouped summary by feature showing timestamp, agent, token counts, and a one-line summary per run. Token counts are optional — agents pass `0` when they cannot measure.

### Pathly Setup (Adapter Installer)

Install agent files into AI host tools (from the [pathly-adapters](https://github.com/hamilton-sky/pathly-adapters) repo):

```bash
pip install -e .
pathly-setup                      # detect hosts; no writes
pathly-setup --dry-run            # preview what would be written
pathly-setup --apply              # install into all detected hosts
pathly-setup claude --apply       # install for Claude Code only
pathly-setup codex --apply        # install for Codex only
```

### Developer Install

Install both packages for local development and tests:

```bash
# Adapters (separate repo — github.com/hamilton-sky/pathly-adapters):
git clone https://github.com/hamilton-sky/pathly-adapters ../pathly-adapters
pip install -e ../pathly-adapters

# Engine (this repo):
pip install -e pathly-engine/

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
The other skills (`/pathly storm`, `/pathly plan`, `/pathly prd-import`) exist for manual control
when you need to jump into the middle of a pipeline. (`/pathly bmad-import` is an alias for `prd-import`.)

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
- Codex plugin support is available through
  `adapters/codex/.codex-plugin/plugin.json`.
- Cursor, Windsurf, BMAD, and generic prompt adapters are planned in
  [pathly-adapters/docs/MULTI_TOOL_DESIGN.md](https://github.com/hamilton-sky/pathly-adapters/blob/master/docs/MULTI_TOOL_DESIGN.md).
- Python 3.11+ is required for local development and tests.
- CI runs the test suite on Python 3.11, 3.12, and 3.13.
- The Python package exposes the `pathly` CLI used by local development,
  smoke tests, and adapter wrappers.

---

## Development and tests

Install development dependencies:

```bash
git clone https://github.com/hamilton-sky/pathly-adapters ../pathly-adapters
pip install -e ../pathly-adapters
pip install -e pathly-engine/
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

Pathly uses a **FSM-style command set**. Eight core commands move the pipeline forward;
four specialized commands handle specific situations; the catch-all routes anything else.

### Start here

```text
/pathly start           ← welcome screen + full journey map
/pathly po              ← clarify requirements first (step 0 for ambiguous features)
/pathly storm           ← brainstorm the approach with the architect
/pathly go              ← director reads state and decides what to do next
```

### Move the pipeline

```text
/pathly build           ← implement the next conversation
/pathly pause           ← save state and exit cleanly
/pathly meet            ← consult a role mid-flow (context-aware menu)
/pathly end             ← wrap up, offer retro
```

### When you know what you want

```text
/pathly add password reset          ← director routes (new feature)
/pathly fix the broken checkout     ← director routes (bug → debug pipeline)
/pathly continue the login work     ← director routes (resume)
/pathly review my current changes   ← director routes (review diff)
```

### Specialized entry points

```text
/pathly debug <symptom>     ← bug pipeline: trace → fix → verify
/pathly explore <question>  ← read-only codebase Q&A
/pathly verify              ← check for stale feedback or FSM drift
/pathly help                ← state-aware menu
/pathly help --doctor       ← diagnose stuck state, orphan files, pipeline drift
```

### Explicit pipeline control (advanced)

```text
/pathly flow password-reset strict     ← full pipeline, chosen rigor
/pathly flow navbar-copy nano          ← tiny change, direct to build
/pathly flow checkout build            ← skip to build stage
/pathly flow payment fast              ← no pause points
```

---

## Docs

Engine documentation lives in `pathly-engine/docs/`:

| Doc | What's in it |
|---|---|
| [pathly-engine/docs/FLOW_DIAGRAM.md](pathly-engine/docs/FLOW_DIAGRAM.md) | Full pipeline flow — Mermaid overview, FSM state transitions, feedback routing loops, file outputs per stage |
| [pathly-engine/docs/FAST_MODE_FLOW.md](pathly-engine/docs/FAST_MODE_FLOW.md) | Fast mode flow — auto-advance vs hard stops |
| [pathly-engine/docs/ARCHITECTURE.md](pathly-engine/docs/ARCHITECTURE.md) | Agent roles and boundaries, consultation policy, feedback routing, workflow files, rigor modes, FSM command map |
| [pathly-engine/docs/ORCHESTRATOR_FSM.md](pathly-engine/docs/ORCHESTRATOR_FSM.md) | Deterministic state machine model, events, recovery, guards |
| [pathly-engine/docs/FEEDBACK_PROTOCOL.md](pathly-engine/docs/FEEDBACK_PROTOCOL.md) | Each feedback file format with templates + escalation rules |
| [pathly-engine/docs/SECURITY.md](pathly-engine/docs/SECURITY.md) | Security/reliability posture, risks, mitigations, and production checklist |
| [pathly-engine/docs/PRODUCTION_READINESS.md](pathly-engine/docs/PRODUCTION_READINESS.md) | Engine release criteria: FSM tests, team-flow driver, CLI commands, hook policy, state recovery |
| [pathly-engine/docs/CONCEPTS.md](pathly-engine/docs/CONCEPTS.md) | Philosophy — why files as protocol, why feedback loops |
| [pathly-engine/docs/PATHLY_ARCHITECTURE.md](pathly-engine/docs/PATHLY_ARCHITECTURE.md) | Orchestrator, runners, team_flow packages; STATE.json layout; Python CLI; agent spawning |
| [pathly-engine/docs/TROUBLESHOOTING.md](pathly-engine/docs/TROUBLESHOOTING.md) | FSM recovery, state consistency, common stuck states |
| [pathly-engine/docs/SYSTEM_REVIEW.md](pathly-engine/docs/SYSTEM_REVIEW.md) | Engine strengths, risks, design decisions, hardening recommendations |
| [pathly-engine/docs/examples/](pathly-engine/docs/examples/) | Worked pipeline examples (add-cost-meter and routing guides) |

For adapter-specific docs (install mechanics, host deployment, stitch pipeline, marketplace):
see [github.com/hamilton-sky/pathly-adapters](https://github.com/hamilton-sky/pathly-adapters) — `docs/` folder.

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
| `web-researcher` | Sonnet | WebSearch, WebFetch | Web-only research; cannot touch local files |

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

### FSM Control Commands

| Command | What it does |
|---|---|
| `/pathly start` | Welcome screen — shows the full `po → storm → go → build → end` journey map; 5-option menu |
| `/pathly go [intent]` | Director entry: reads project state and routes to the right skill; catch-all for free-form intent |
| `/pathly storm [topic]` | Architect explores the idea with ASCII diagrams → `STORM_SEED.md` |
| `/pathly build` | Implements the next TODO conversation (alias: `go continue`) |
| `/pathly pause` | Saves session state cleanly; resume with `/pathly go` |
| `/pathly meet [feature]` | Context-aware role consultation: shows different agents based on current FSM state; writes consult note; offers planner/architect promotion |
| `/pathly end` | Session wrap-up: offers retro for any in-progress feature, then closes |
| `/pathly help [feature]` | State-aware menu; `--doctor` diagnoses stuck FSM and orphan files |

### Specialized Commands

| Command | What it does |
|---|---|
| `/pathly po [feature]` | Product Owner session: structured Q&A → `PO_NOTES.md`; offered as step 0 in the journey map |
| `/pathly debug <symptom>` | Bug pipeline: scout traces → builder fixes → tester verifies before + after |
| `/pathly explore <question>` | Investigation mode: answer codebase questions without building anything |
| `/pathly verify [feature]` | Checks orphan/expired feedback files (TTL default 168h), PROGRESS drift, dead code references |

### Pipeline Internals (used by director / `go`)

| Skill | What it does |
|---|---|
| `team-flow <feature> [rigor]` | Full pipeline: discovery→plan→build×N→test→retro with rigor escalator |
| `review` | Reviewer audits code; trivial findings tagged `[AUTO_FIX]` for batch apply |
| `retro <feature>` | Writes RETRO.md with cost summary + appends to LESSONS_CANDIDATE.md |
| `lessons` | Promotes candidate lessons to LESSONS.md for planner |
| `archive <feature>` | Moves completed plan to `plans/.archive/` |
| `prd-import <feature> <prd.md> [rigor]` | Translates any PRD (generic, AI-generated, or BMAD) into plan files; `/pathly bmad-import` is an alias |

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

Every feedback file carries a YAML frontmatter block:
```yaml
---
created_at: 2026-05-04T08:12:00Z
created_by_event: evt-abc123
ttl_hours: 168
---
```
`/pathly verify` and `/pathly help --doctor` use this to detect orphan files (event not in current log) and expired files (TTL elapsed) — both are safe to delete automatically.

- Default TTL is **168 hours (1 week)** — avoids false positives when you pause a feature for a few days.
- The `created_by_event` ID also anchors the **retry budget**: the feedback loop tracks retries per event ID, not per conversation number, so replanning a conversation doesn't silently reset the counter.

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
    └── templates/pathly plan/             ← plan file templates used by /pathly plan and /pathly prd-import
        └── *.template.md
```

Run `pathly-setup --apply` after cloning to install agent files into all detected hosts.

---

## Philosophy

1. **Agent = behavioral contract, not persona.** The role defines HOW the agent thinks, not a character it plays.
2. **Files are the contract between roles.** No agent calls another directly. State lives on disk and is recovered by the orchestrator FSM.
3. **Human checkpoints are the point.** The pipeline pauses at every stage transition.
4. **Feedback loops, not a linear chain.** Wrong problem routes to the right role automatically.

See [docs/ARCHITECTURE_AGENTS.md](docs/ARCHITECTURE_AGENTS.md) for the full architecture.

