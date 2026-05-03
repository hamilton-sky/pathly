# Claude Agents Framework

A role-based agent system for Claude Code where **files are the protocol**,
**behavioral contracts** define how each agent thinks, and **feedback loops**
route issues back to the right agent automatically.

## What this is

8 specialized agents + 7 lifecycle skills that give Claude Code a structured
development pipeline: brainstorm → plan → implement → review → test → retro.

Unlike conversation-based workflows, state lives on disk. Agents hand off via
files. An open feedback file blocks the pipeline. A deleted file means resolved.

---

## Quick install

**Linux / macOS:**
```bash
git clone https://github.com/hamilton-sky/claude-agents-framework
cd claude-agents-framework
chmod +x install.sh && ./install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/hamilton-sky/claude-agents-framework
cd claude-agents-framework
.\install.ps1
```

Then open any project in Claude Code and run:
```
/team-flow <feature-name>
```

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
| `orchestrator` | Haiku | Pipeline sequencing | Spawns agents, routes feedback files |

---

## The 7 Skills

| Skill | Command | What it does |
|---|---|---|
| `storm` | `/storm` | Architect explores the idea with ASCII diagrams |
| `plan` | `/plan <feature>` | Creates `plans/<feature>/` with 8 files |
| `build` | `/build <feature>` | Implements the next TODO conversation |
| `review` | `/review` | Reviewer audits code against rules |
| `retro` | `/retro <feature>` | Writes RETRO.md with seed for next storm |
| `team-flow` | `/team-flow <feature>` | Full pipeline: storm→plan→build×N→retro |
| `bmad-import` | `/bmad-import <feature> <prd.md>` | Translates a BMAD PRD into plan files |

---

## The Feature Pipeline

```
/team-flow payment-flow

  Stage 1 — Storm      architect explores idea  →  STORM_SEED.md
       PAUSE: "Ready to plan?"
  Stage 2 — Plan       planner creates 8 files  →  plans/payment-flow/
       PAUSE: "Review plan. go / stop"
  Stage 3 — Implement  builder + reviewer loop  →  code + PROGRESS.md
       ├─ builder hits blocker → IMPL_QUESTIONS.md → planner
       ├─ builder hits design gap → DESIGN_QUESTIONS.md → architect
       └─ reviewer finds violation → REVIEW_FAILURES.md → builder
       PAUSE: "Commit. continue / stop"
  Stage 4 — Test       tester maps ACs to tests → TEST_FAILURES.md → builder
  Stage 5 — Retro      quick writes RETRO.md
```

Add `auto` to skip pause points:
```
/team-flow payment-flow auto
```

---

## Feedback File Protocol

5 files in `plans/<feature>/feedback/`. **File exists = issue open. Deleted = resolved.**

| File | Written by | Resolved by |
|---|---|---|
| `ARCH_FEEDBACK.md` | reviewer | architect |
| `REVIEW_FAILURES.md` | reviewer | builder |
| `IMPL_QUESTIONS.md` | builder | planner |
| `DESIGN_QUESTIONS.md` | builder | architect |
| `TEST_FAILURES.md` | tester | builder |

`ARCH_FEEDBACK.md` is blocking — no building until architect resolves it.

---

## BMAD Integration

If you use BMAD for discovery and PRD generation, import its output directly:

```
/bmad-import hotel-search docs/hotel-search-prd.md
```

This reads the BMAD PRD and generates all 8 plan files — translating:
- Acceptance Criteria → verify commands
- Edge Cases → workflow conversation prompts
- Out of Scope → Do NOT lists in every builder prompt

Then continue normally with `/build hotel-search` or `/team-flow hotel-search`.

---

## What gets installed

```
~/.claude/
├── agents/          ← 8 behavioral contracts (.md files)
├── skills/          ← 7 lifecycle skills (storm, plan, build, ...)
│   └── */SKILL.md
└── templates/plan/  ← 8 plan file templates
    └── *.template.md
```

Your existing `~/.claude/` content is backed up before install.

---

## Philosophy

1. **Agent = behavioral contract, not persona.** The role defines HOW the agent thinks, not a character it plays.
2. **Files are the contract between roles.** No agent calls another directly. State lives on disk.
3. **Human checkpoints are the point.** The pipeline pauses at every stage transition.
4. **Feedback loops, not a linear chain.** Wrong problem routes to the right role automatically.

See [docs/ARCHITECTURE_AGENTS.md](docs/ARCHITECTURE_AGENTS.md) for the full architecture.
