# Multi-Tool Architecture Design

How to evolve this framework from Claude Code-only to tool-agnostic,
so the same agent contracts and skills work in Cursor, Windsurf, BMAD,
or any AI tool — without rewriting the core.

---

## The Problem with Today's Structure

Everything lives in Claude Code format:

```
~/.claude/agents/architect.md     ← Claude Code frontmatter
~/.claude/skills/plan/SKILL.md    ← Claude Code skill format
```

Someone using Cursor cannot install this. Someone using Windsurf cannot install this.
The knowledge (behavioral contracts, skill steps) is tool-agnostic. The packaging is not.

---

## The Solution: Core + Adapters

Separate WHAT the agents know from HOW each tool loads them.

```
pathly/
│
├── core/                          ← tool-agnostic source of truth
│   ├── agents/                    ← pure markdown behavioral contracts
│   │   ├── architect.md           ← no frontmatter, no tool syntax
│   │   ├── planner.md
│   │   ├── builder.md
│   │   ├── reviewer.md
│   │   ├── tester.md
│   │   ├── orchestrator.md
│   │   └── quick.md
│   ├── prompts/                   ← skill steps as numbered instructions
│   │   ├── storm.md
│   │   ├── plan.md
│   │   ├── build.md
│   │   ├── review.md
│   │   ├── retro.md
│   │   ├── team-flow.md
│   │   └── bmad-import.md
│   └── templates/plan/            ← same 8 plan templates (already generic)
│       └── *.template.md
│
├── adapters/
│   ├── claude-code/               ← wraps core/ into ~/.claude/ format
│   │   ├── install.sh
│   │   ├── install.ps1
│   │   └── wrap.sh                ← adds Claude Code frontmatter to core agents
│   │
│   ├── cursor/                    ← wraps core/ into Cursor rules format
│   │   ├── install.sh
│   │   └── .cursor/rules/         ← agents become .mdc rule files
│   │
│   ├── windsurf/                  ← wraps core/ into Windsurf format
│   │   ├── install.sh
│   │   └── .windsurf/rules/
│   │
│   ├── bmad/                      ← wraps core/ into .chatmode.md files
│   │   ├── install.sh
│   │   └── .bmad/
│   │
│   └── generic/                   ← raw prompts, no tool required
│       └── prompts/               ← copy-paste into any AI chat
│
├── docs/
│   ├── ARCHITECTURE_AGENTS.md
│   ├── CONCEPTS.md
│   ├── FEEDBACK_PROTOCOL.md
│   ├── ORCHESTRATOR_FSM.md
│   └── MULTI_TOOL_DESIGN.md       ← this file
│
└── README.md
```

---

## What "core agent" looks like (no tool syntax)

```markdown
# Architect

## Role
Think about how to build things technically — layers, dependency
direction, trade-offs, design decisions.

## Single Responsibility
Resolve architectural questions. Never implement.

## What I write
- STORM_SEED.md after /storm
- ARCHITECTURE_PROPOSAL.md in plans/<feature>/
- Resolves: ARCH_FEEDBACK.md, DESIGN_QUESTIONS.md (deletes when done)

## How I think
1. Read CLAUDE.md to learn the project's layer structure
2. Check .claude/rules/ for per-layer contracts
3. Identify which layers this feature touches
4. Design dependency direction before any implementation starts
5. Write decisions — never leave a design ambiguous

## Constraints
- Never implement. If implementation is needed, write DESIGN_QUESTIONS.md
- Never approve a design that violates the three-layer contract
- Opus model — deep reasoning, not speed
```

An adapter then wraps this in the tool-specific format. For Claude Code:

```markdown
---
name: architect
model: claude-opus-4-5
description: Technical architecture — layers, trade-offs, design decisions
---

# Architect
[...same body as core...]
```

For Cursor (`.cursor/rules/architect.mdc`):

```markdown
---
description: Use when making architecture decisions
globs: ["**/*.py", "**/*.ts"]
alwaysApply: false
---

# Architect
[...same body as core...]
```

---

## What "core prompt" looks like (skill steps, no tool format)

```markdown
# plan — Create a feature plan

## Input
- Feature name (argument)
- Optional: plans/STORM_SEED.md (pre-filled from /storm)

## Output
- plans/<feature>/ with rigor-specific files (4 in lite, 8 in standard/strict)

## Steps

### Step 1: Understand the feature
Check if plans/STORM_SEED.md exists.
If yes: read it, pre-fill interview answers, confirm with user, delete it.
If no: interview — what does it do? which layers? dependencies? complexity?

### Step 2: Research the codebase
[...same steps as today...]
```

Each tool adapter wraps this in its slash-command or workflow format.

---

## Migration Path: Today → Tomorrow

The migration is **non-breaking and additive**. No existing installs break.

```
TODAY (v1)                    TOMORROW (v2)
──────────────────────────    ──────────────────────────────────
agents/*.md                   core/agents/*.md  (body identical)
  (with CC frontmatter)         (frontmatter stripped to separate file)

skills/*/SKILL.md             core/prompts/*.md (steps identical)
  (with CC frontmatter)         (steps extracted, frontmatter in adapter)

install.sh / install.ps1      adapters/claude-code/install.sh
  (copies directly)             (wraps core/ then copies)
```

**Three concrete steps to migrate:**

1. Move `agents/` body content → `core/agents/` (strip frontmatter)
2. Move `skills/*/SKILL.md` steps → `core/prompts/` (strip frontmatter)
3. Create `adapters/claude-code/` that re-adds the frontmatter on install

The `adapters/claude-code/install.sh` becomes a two-stage script:
- Stage 1: prepend frontmatter to each core agent → write to a tmp dir
- Stage 2: copy tmp dir to `~/.claude/` (same as today)

Users who installed v1 just re-run `install.sh` — it overwrites cleanly.

---

## When to do this

**Ship v1 now** (Claude Code only). It works today, delivers value today.

**Migrate to v2 when:**
- Someone asks for Cursor support (real demand signal)
- You want to publish to a broader audience
- You start maintaining BMAD adapters in parallel

The v1 → v2 migration is ~2-3 hours of restructuring. It does not require
rewriting any agent contracts or skill steps — only the packaging changes.

---

## Versioning

Tag v1 on GitHub before migrating:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Then restructure on a branch (`feat/multi-tool`), PR it as v2.
Anyone pinned to v1 is unaffected. Anyone re-running install gets v2.
