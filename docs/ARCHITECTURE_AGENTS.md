# Claude Skills Architecture

A role-based agent system where **files are the protocol** between roles,
**behavioral contracts** define how each agent thinks, **human checkpoints**
keep you in control at every stage transition, and **feedback loops** route
issues back to the right agent automatically.

---

## Philosophy

Four principles drive this architecture:

1. **Agent = role, not persona.** An agent is a behavioral contract — it defines HOW
   something thinks, not a character it pretends to be. `architect` thinks in layers
   and trade-offs. `planner` thinks in user value. `builder` stays in scope and verifies.
   The role is stable; it does not change with the project.

2. **Files are the contract between roles.** Roles do not call each other directly.
   Each role writes a file when its job is done; the next role reads that file as input.
   State lives on disk — not in memory, not in conversation context. Any role can stop
   and resume because the file is always there.

3. **Human checkpoints are the point.** The pipeline pauses at every stage transition
   and waits for explicit acknowledgement. This is not a limitation — it is the design.
   Checkpoints are where wrong assumptions get caught cheaply, before expensive work begins.

4. **Feedback loops, not a linear chain.** When a reviewer finds an architectural flaw,
   it does not just report to chat — it writes a feedback file that routes back to the
   architect. When a builder hits a technical blocker, it asks the architect, not the planner.
   The right problem goes to the right role automatically.

---

## Two Scopes

```
~/.claude/
══════════════════════════════
agents/   ← roles (any project)
skills/   ← lifecycle abilities
templates/← plan file templates
ARCHITECTURE.md   ← this file
FEEDBACK_PROTOCOL.md ← feedback file formats
```

**Global** (`~/.claude/`) — available in every project on this machine.
Agents and lifecycle skills belong here. They are generic; they read the project's
CLAUDE.md to understand local conventions.

---

## The 8 Agents

Each agent is a `.md` file in `~/.claude/agents/` with a frontmatter block:
`name`, `role`, `model`, `skills`, `description` — then behavioral rules in the body.

```
~/.claude/agents/
│
├─ architect.md      role: architect      model: opus
│   "How should this be built technically?"
│   Thinks in layers, dependency directions, design trade-offs.
│   Resolves: ARCH_FEEDBACK.md, DESIGN_QUESTIONS.md
│   skills: [storm]
│
├─ planner.md        role: product-owner  model: sonnet
│   "What needs to be built, for whom, verified how?"
│   Writes user stories, acceptance criteria, conversation decomposition.
│   Resolves: IMPL_QUESTIONS.md
│   skills: [storm, plan]
│
├─ builder.md        role: executor       model: sonnet
│   "Build exactly what was planned. No more, no less."
│   Reads before editing. Verifies before reporting done.
│   Writes: IMPL_QUESTIONS.md ([REQ] — requirement ambiguity → planner)
│           DESIGN_QUESTIONS.md ([ARCH] — technical blocker → architect)
│           both files if [UNSURE] — correct owner discards
│   Resolves: REVIEW_FAILURES.md, TEST_FAILURES.md
│   skills: [build]
│
├─ tester.md         role: tester         model: sonnet
│   "Does the code match the acceptance criteria?"
│   Maps each criterion to a test. Reports bugs, never fixes them.
│   Writes: TEST_FAILURES.md
│   skills: [test]
│
├─ quick.md          role: analyst        model: haiku
│   "Fast answer. 2 tool calls max."
│   Direct, no preamble, returns value or path immediately.
│   skills: [retro]
│
├─ reviewer.md       role: reviewer       model: sonnet
│   "Find what's wrong before it ships."
│   Adversarial. Reports violations with file + rule reference. Never edits.
│   Writes: ARCH_FEEDBACK.md (structural violations)
│           REVIEW_FAILURES.md (implementation violations)
│   skills: [review, security-review]
│
├─ discoverer.md     role: discoverer     model: sonnet
│   "Trace before generating. Follow what's visible."
│   Navigates live sites, captures a11y trace data, pauses at auth.
│   skills: project-local (defined per project in .claude/skills/)
│
└─ orchestrator.md   role: orchestrator   model: haiku
    "Sequence the pipeline. Spawn the right agent. Route feedback files."
    Checks for feedback files after every spawn. Never advances past open feedback.
    skills: [team-flow]
```

### Model tier reasoning

```
opus    ← architect      deep reasoning, architecture judgment
sonnet  ← planner        balanced, requirements thinking
sonnet  ← builder        code execution, following instructions
sonnet  ← tester         careful verification, gap analysis
sonnet  ← reviewer       adversarial analysis, rule checking
sonnet  ← discoverer     site navigation, pattern recognition
haiku   ← quick          fast lookups, no reasoning needed
haiku   ← orchestrator   sequencing + routing, no deep reasoning needed
```

---

## Skills by Scope

Skills are `.md` files in a `<skill-name>/SKILL.md` structure with frontmatter:
`name`, `description`, `argument-hint` — then step-by-step instructions in the body.

### Global lifecycle skills (`~/.claude/skills/`)

```
team-flow      ← full pipeline with feedback loops: discovery→plan→build→test→retro
storm          ← brainstorm a feature idea; write STORM_SEED.md on /stop plan
plan           ← interview + research → create plans/<feature>/ with 8 files
build          ← read PROGRESS.md → implement next TODO conversation → verify
review         ← check code against architectural rules; report violations
retro          ← ask 3 questions → write RETRO.md + append to LESSONS_CANDIDATE.md
lessons        ← promote repeated patterns from LESSONS_CANDIDATE.md → LESSONS.md
archive        ← move completed plan to plans/.archive/ (requires RETRO.md + all DONE)
prd-import     ← read any PRD file → translate ACs + edge cases → generate all 8 plan files
```

### Project-local skills (`.claude/skills/`)

Defined per-project — not documented here. See the project's own `.claude/` folder.

---

## BMAD Integration

The `bmad-import` skill bridges BMAD discovery output into this pipeline.
BMAD handles the discovery and requirements phase; this framework handles the build.

```
BMAD Phase (external — any tool)
  Analyst interviews user
  PM writes PRD → docs/<feature>-prd.md

Bridge — one command:
  /bmad-import <feature> docs/<feature>-prd.md
    reads PRD
    translates: ACs → verify commands
                edge cases → workflow conversation scopes
                out-of-scope → Do NOT lists in every prompt
    generates: plans/<feature>/ (all 8 files)

Agent Pipeline (this framework)
  /team-flow <feature>    ← or /build <feature> per conversation
```

**The handoff is one file.** BMAD writes a PRD. `bmad-import` reads it. The
agent pipeline runs from there. No shared infrastructure, no coupling.

### Global vs. project-local scope

```
~/.claude/                    Global — available in every project
  agents/                     8 behavioral contracts
  skills/                     8 lifecycle skills (including archive + prd-import)
  templates/plan/             8 plan file templates

your-project/                 Local — teaches agents YOUR rules
  CLAUDE.md                   Architecture overview, run commands, conventions
  .claude/rules/              Project conventions (naming, layer rules, patterns)
  .claude/skills/             Project-specific tools (custom validators, generators)
```

Agents read `CLAUDE.md` + `.claude/rules/` during the plan step to learn the
project's conventions. The same agents work in any project — only the rules files change.

---

## The Feature Pipeline

Start any feature with one command:

```
/team-flow <feature-name>            ← pauses at every stage (default)
/team-flow <feature-name> fast       ← runs to completion, no pauses
/team-flow <feature-name> build      ← skip discovery+plan, resume build
/team-flow <feature-name> test       ← skip to test stage only
/team-flow <feature-name> build fast ← resume build, no pauses
```

### Pipeline with feedback loops

```
You: /team-flow payment-flow
              │
              ▼
   ┌────────────────────┐
   │  Stage 1 — Storm   │  architect (opus) explores idea technically
   │                    │  → writes STORM_SEED.md on /stop plan
   └─────────┬──────────┘
         PAUSE ← "Ready to plan? yes / no"
              │
              ▼
   ┌────────────────────┐
   │  Stage 2 — Plan    │  planner (sonnet) runs /plan
   │                    │  reads STORM_SEED.md if present
   │                    │  → writes plans/<feature>/ (8 files)
   └─────────┬──────────┘
         PAUSE ← "Review plan. go / stop"
              │
              ▼
   ┌──────────────────────────────────────────────┐
   │  Stage 3 — Implement + Review Loop           │
   │                                              │
   │  ┌─────────┐                                 │
   │  │ builder │── [REQ] IMPL_QUESTIONS.md ──► planner │
   │  │(sonnet) │── [ARCH] DESIGN_QUESTIONS.md ─► arch. │
   │  │         │── [UNSURE] → both files               │
   │  └────┬────┘                                 │
   │       │ code written                         │
   │       ▼                                      │
   │  ┌──────────┐                                │
   │  │ reviewer │── ARCH_FEEDBACK.md ──► arch.   │
   │  │ (sonnet) │── REVIEW_FAILURES.md ─► build. │
   │  └────┬─────┘                                │
   │       │ PASS                                 │
   │  PAUSE ← "Commit. continue / stop"           │
   │  (repeats for each TODO conversation)        │
   └─────────────────────┬────────────────────────┘
                         │ all conversations DONE
                         ▼
   ┌──────────────────────────────────────────────┐
   │  Stage 4 — Test + Fix Loop                   │
   │                                              │
   │  ┌────────┐                                  │
   │  │ tester │── TEST_FAILURES.md ──► builder   │
   │  │(sonnet)│                                  │
   │  └────┬───┘                                  │
   │       │ all criteria PASS                    │
   │  PAUSE ← "done / fix"                        │
   └─────────────────────┬────────────────────────┘
                         │
                         ▼
   ┌────────────────────┐
   │  Stage 5 — Retro   │  quick (haiku) runs /retro
   │                    │  → writes RETRO.md
   └────────────────────┘
```

---

## Feedback File Protocol

Feedback files live in `plans/<feature>/feedback/`.
**A file existing = issue open. No file = resolved.**
The orchestrator checks after every agent spawn. Never advances past open feedback.

### The 5 feedback files

| File | Written by | Resolved by | When |
|---|---|---|---|
| `ARCH_FEEDBACK.md` | reviewer | architect | structural/architectural violation found |
| `REVIEW_FAILURES.md` | reviewer | builder | implementation-level bug found |
| `IMPL_QUESTIONS.md` | builder | planner | requirement is ambiguous ("what should this do?") |
| `DESIGN_QUESTIONS.md` | builder | architect | technical blocker ("how is this possible?") |
| `TEST_FAILURES.md` | tester | builder | acceptance criterion FAIL or NOT COVERED |

### Escalation paths

```
reviewer ──► ARCH_FEEDBACK.md    ──► architect  (redesign → builder re-implements)
         └─► REVIEW_FAILURES.md  ──► builder    (fix → reviewer re-checks)

builder  ──► IMPL_QUESTIONS.md   ──► planner    ([REQ] — clarify → builder continues)
         └─► DESIGN_QUESTIONS.md ──► architect  ([ARCH] — resolve → builder continues)
         (both files if [UNSURE] — correct owner discards)

tester   ──► TEST_FAILURES.md    ──► builder    (fix → tester re-checks)
```

**Tag rule for builder:**
- `[REQ]` = "what should this do?" → IMPL_QUESTIONS.md → planner
- `[ARCH]` = "how is this technically possible?" → DESIGN_QUESTIONS.md → architect
- `[UNSURE]` = genuinely unclear → write to both files, correct owner discards

### Resolution rules

- Agent that resolves the issue **deletes the feedback file** when done.
- **Max 2 retry cycles per conversation.** If exceeded: stop and surface to user.
- **ARCH_FEEDBACK blocks all further building.** Must be resolved by architect first.
- Feedback is blocking — pipeline never advances past an open feedback file.

---

## Full Agent Communication Map

```
         ┌─────────────────────────────┐
         │         architect           │
         │          (opus)             │
         │ ◄── ARCH_FEEDBACK.md        │  ← from reviewer
         │ ◄── DESIGN_QUESTIONS.md     │  ← from builder
         │  ──► ARCHITECTURE_PROPOSAL  │  → read by planner + builder
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │          planner            │
         │         (sonnet)            │
         │ ◄── IMPL_QUESTIONS.md       │  ← from builder
         │  ──► plans/<feature>/       │  → read by builder
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │          builder            │◄──── REVIEW_FAILURES.md (from reviewer)
         │         (sonnet)            │◄──── TEST_FAILURES.md   (from tester)
         │  ──► IMPL_QUESTIONS.md      │  → to planner
         │  ──► DESIGN_QUESTIONS.md    │  → to architect
         │  ──► code + PROGRESS.md     │  → read by reviewer + tester
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │         reviewer            │
         │         (sonnet)            │
         │  ──► ARCH_FEEDBACK.md       │  → to architect
         │  ──► REVIEW_FAILURES.md     │  → to builder
         └──────────────┬──────────────┘
                        │ PASS
         ┌──────────────▼──────────────┐
         │          tester             │
         │         (sonnet)            │
         │  ──► TEST_FAILURES.md       │  → to builder
         └──────────────┬──────────────┘
                        │ PASS
         ┌──────────────▼──────────────┐
         │           quick             │
         │          (haiku)            │
         │  ──► RETRO.md               │  → seed for next storm
         └─────────────────────────────┘
```

---

## File-Based Handoff Protocol (Forward Flow)

```
ROLE              WRITES                         READS
──────────────    ───────────────────────────    ──────────────────────────
architect         STORM_SEED.md                  —
(storm)                    │
                            ▼
planner           plans/<feature>/               STORM_SEED.md (then deletes)
(plan)              ├─ USER_STORIES.md
                    ├─ IMPLEMENTATION_PLAN.md
                    ├─ PROGRESS.md
                    ├─ CONVERSATION_PROMPTS.md
                    ├─ HAPPY_FLOW.md
                    ├─ EDGE_CASES.md
                    ├─ ARCHITECTURE_PROPOSAL.md
                    └─ FLOW_DIAGRAM.md
                            │
                            ▼
builder           PROGRESS.md (TODO→DONE/conv)   CONVERSATION_PROMPTS.md
(build)           feedback/*.md if blocked        PROGRESS.md
                            │
                            ▼
reviewer          feedback/ARCH_FEEDBACK.md       changed files (git diff)
(review)          feedback/REVIEW_FAILURES.md     .claude/rules/*.md
                            │ PASS
                            ▼
tester            feedback/TEST_FAILURES.md       USER_STORIES.md
(test)                      │ PASS               (acceptance criteria)
                            ▼
quick             RETRO.md                        PROGRESS.md
(retro)             "Seed for Next Storm"         CONVERSATION_PROMPTS.md
                  LESSONS_CANDIDATE.md (append)
                            │
                            ▼
(optional)        LESSONS.md                      LESSONS_CANDIDATE.md
/lessons            promoted active lessons       plans/.archive/*/RETRO.md
                    max 12, planner reads this
                            │
                            ▼
user              plans/.archive/<feature>/        plans/<feature>/
(archive)           all 8 files + RETRO.md          moved, not deleted
                    recoverable via git             plans/ stays clean
                            │
                            ▼
architect         [next session — new feature]    RETRO.md (from archive)
(storm)
planner           applies LESSONS.md injections   LESSONS.md
(plan)
```

---

## Plan File Traceability

The 8 files in `plans/<feature>/` cross-reference each other — full traceability
from user story to the conversation that implements it.

```
USER_STORIES.md          IMPLEMENTATION_PLAN.md     CONVERSATION_PROMPTS.md
─────────────────        ──────────────────────     ───────────────────────
Story S1.1               Phase 1                    Conversation 1
  Acceptance Criteria      Delivers stories: S1.1     Stories delivered: S1.1
  Edge Cases               Files: ...                 Prompt: ...
  Delivered by:            Verify: ...
    Phase 1 → Conv 1

                          PROGRESS.md
                          ─────────────────────────────────────
                          Story Status table   S1.1: TODO → DONE
                          Conversation table   Conv 1: TODO → DONE
                          Phase Detail table   Phase 1: TODO → DONE
```

---

## Worked Examples

### Example 1 — With BMAD (discovery first)

**Scenario:** Build a hotel search feature on phpTravels. You already ran BMAD and have a PRD.

```
Step 1 — BMAD wrote this file (outside Claude Code):
  docs/phptravels-hotel-search-prd.md
    User Stories: S1 (search), S2 (select hotel)
    ACs: city input, date pickers, results list, book button
    Edge cases: no results, invalid dates
    Out of scope: payment, user accounts

Step 2 — Import it:
  /bmad-import hotel-search docs/phptravels-hotel-search-prd.md

  bmad-import reads the PRD and translates:
    AC "city input exists"        → pytest verify: assert search_page.city_input_visible()
    AC "results show price"       → pytest verify: pytest tests/test_hotel_results.py -k price
    Edge case "no results"        → Conversation 2: handle empty results state
    Out of scope "payment"        → Do NOT: in every conversation prompt

  Output: plans/hotel-search/ (8 files, ready for building)

Step 3 — Build:
  /team-flow hotel-search

  architect reads plans/ + CLAUDE.md + .claude/rules/
    → designs the implementation structure for hotel search
  builder Conversation 1:
    → src/hotel/search.py (search logic + page interactions)
    → tests/test_hotel_search.py
  builder Conversation 2:
    → src/hotel/results.py
    → tests/test_hotel_results.py (no-results edge case)
  reviewer checks architecture + project conventions after each conversation
  tester runs: pytest tests/test_hotel_search.py
  quick writes RETRO.md
```

---

### Example 2 — Without BMAD (plan directly)

**Scenario:** Add drag-and-drop product sorting to SauceDemo. No PRD, you know what you want.

```
Step 1 — Brainstorm (optional):
  /storm

  architect (Opus) explores the idea:
    "drag-and-drop needs mouse_down + drag_to + mouse_up sequence"
    "SauceDemo inventory page — items are divs, no native drag API"
    "need to identify drag targets by their data attributes"
  → writes plans/STORM_SEED.md with decisions + open questions

Step 2 — Plan:
  /plan saucedemo-drag-drop

  planner reads STORM_SEED.md (pre-filled answers)
  interviews you on anything missing
  reads CLAUDE.md + .claude/rules/ to learn project conventions
  generates plans/saucedemo-drag-drop/ (8 files):
    CONVERSATION_PROMPTS.md has 2 conversations:
      Conv 1: implement drag interaction logic + unit tests
      Conv 2: write integration test for full drag-sort flow

Step 3 — Build one conversation at a time:
  /build saucedemo-drag-drop     ← implements Conv 1, pauses
  /build saucedemo-drag-drop     ← implements Conv 2, pauses

  Or run everything:
  /team-flow saucedemo-drag-drop

Step 4 — Verify:
  pytest tests/test_drag_sort.py
```

**Key difference from Example 1:** No PRD file. `/plan` does the interview itself.
The rest of the pipeline is identical.

---

### Decision guide: BMAD or /plan?

| Situation | Use |
|---|---|
| You have a BMAD PRD already | `/bmad-import <feature> <prd.md>` |
| Complex feature, need discovery first | Run BMAD → then `/bmad-import` |
| You know what you want, no PRD | `/plan <feature>` (interview mode) |
| Quick feature, just start building | `/storm` then `/plan` then `/build` |

---

## Quick Reference

```bash
# Recommended entry (new users)
/help                            ← detect state → numbered menu
                                 #   pick [1] → describe in plain English → /go routes you

# Plain English entry
/go                              ← prompts "What do you want?" → classifies → routes
/go <what you want>              ← skip the prompt, routes immediately

# Direct pipeline entry
/team-flow <feature>

# Run with no pauses
/team-flow <feature> fast

# Resume mid-pipeline
/team-flow <feature> build       ← skip to build stage
/team-flow <feature> test        ← skip to test stage
/team-flow <feature> plan        ← skip discovery, start planning
/team-flow <feature> build fast  ← resume build, no pauses

# Individual stages (manual control)
/storm                           ← architect explores the idea
/plan <feature>                  ← planner creates plans/<feature>/
/build <feature>                 ← builder implements next conversation
/retro <feature>                 ← quick runs the retrospective + extracts lessons
/lessons                         ← promote candidate lessons → LESSONS.md (active)
/archive <feature>               ← move completed plan to plans/.archive/

# Code quality
/review                         ← reviewer checks staged changes

# Site/UI discovery (project-local skills — if installed in .claude/skills/)
/discover-site <url>            ← discoverer traces a live site
/generate-poms                  ← discoverer generates project-specific page objects
```

---

## Directory Map

```
~/.claude/
├── ARCHITECTURE.md         ← this file
├── FEEDBACK_PROTOCOL.md    ← feedback file formats + escalation rules
├── agents/
│   ├── README.md
│   ├── architect.md
│   ├── planner.md
│   ├── builder.md
│   ├── tester.md
│   ├── quick.md
│   ├── reviewer.md
│   ├── discoverer.md
│   └── orchestrator.md
├── skills/
│   ├── team-flow/SKILL.md
│   ├── storm/SKILL.md
│   ├── plan/SKILL.md
│   ├── build/SKILL.md
│   ├── review/SKILL.md
│   ├── retro/SKILL.md
│   ├── lessons/SKILL.md
│   ├── archive/SKILL.md
│   └── prd-import/SKILL.md
├── hooks/
│   └── classify_feedback.py    ← PostToolUse/Write — auto-tags IMPL_QUESTIONS.md
└── templates/plan/
    ├── USER_STORIES.template.md
    ├── IMPLEMENTATION_PLAN.template.md
    ├── PROGRESS.template.md
    ├── CONVERSATION_PROMPTS.template.md
    ├── HAPPY_FLOW.template.md
    ├── EDGE_CASES.template.md
    ├── ARCHITECTURE_PROPOSAL.template.md
    └── FLOW_DIAGRAM.template.md

.claude/  (project-local — defined per project, not documented here)
├── rules/    ← project-specific conventions
├── skills/   ← project-specific tools
└── hooks/    ← project-specific guards
```
