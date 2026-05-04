# Scout Delegation — User Stories

## Context

The builder agent previously had two options for mid-task context: `quick` (max 2 tool calls, 1-line answer)
or write a feedback file. There was no middle tier for investigations requiring 3–15 file reads before
implementation begins.

This feature defines a **4-level information gathering ladder** and rolls it out across all five agent roles:

| Level | Agent | Scope | Cap |
|-------|-------|-------|-----|
| 0 — Pre-flight | All | Glob/Grep before any tool call | — |
| 1 — Quick | All | ≤ 2 tool calls, 1-line answer | shared 4-total cap |
| 2 — Scout | builder, architect, reviewer, tester | Cross-file codebase investigation | shared 4-total cap |
| 3 — Web | architect, planner | External design patterns, library docs | shared 4-total cap |

Global rule: **at most 4 sub-agents total per session/conversation**, shared across all levels.
Sub-agents are terminal — they cannot spawn further agents.

---

## Stories

### S1.1: Scout agent file exists as a named, read-only agent ✅ DONE
**As a** builder, **I want** a dedicated agent file at `agents/scout.md`, **so that** I can spawn
it via `subagent_type="scout"` and `model=haiku` to investigate codebase structure without modifying any file.

**Acceptance Criteria:**
- [x] `agents/scout.md` exists with valid frontmatter (name, role, model)
- [x] Explicit language forbidding file edits, feedback file creation, and spawning further agents
- [x] Structured Findings output format (`## Findings`, `## Recommendation`, `## Ambiguities`)
- [x] Quick vs Scout decision table

---

### S1.2: Builder knows when to use scout vs quick ✅ DONE
**As a** builder, **I want** a clear sub-agent section in `agents/builder.md`, **so that** I reach
for the right tool without rereading agent definitions.

**Acceptance Criteria:**
- [x] `agents/builder.md` contains an "Information gathering — sub-agents" section
- [x] Section includes max-4 cap (not max-3)
- [x] Summarize-before-editing rule marked as **load-bearing**
- [x] Builder is sole implementation owner; sub-agents advisory only
- [x] Conflict resolution rule: factual conflict → third scout; architectural → DESIGN_QUESTIONS.md [ARCH]
- [x] Web-researcher explicitly excluded from builder

---

### S2.1: Build skill documents scout constraints
**As a** builder reading `skills/build/SKILL.md`, **I want** a scout delegation section, **so that**
the max-4 cap and summarize rule are impossible to miss even without reading `agents/builder.md`.

**Acceptance Criteria:**
- [ ] `skills/build/SKILL.md` contains a scout delegation section
- [ ] States the max-4 sub-agents limit
- [ ] States the summarize-before-editing rule
- [ ] States scouts are read-only and cannot create feedback files

**Delivered by:** Phase 3 → Conversation 2

---

### S2.2: Static assertions verify all load-bearing rules
**As a** framework maintainer, **I want** grep assertions that confirm load-bearing rules are present,
**so that** a future edit that removes a key constraint is caught immediately.

**Acceptance Criteria:**
- [ ] `agents/scout.md` grep for explicit no-edit language passes
- [ ] `agents/builder.md` grep for builder as sole implementation owner passes
- [ ] `agents/builder.md` grep for max-4 cap passes
- [ ] `skills/build/SKILL.md` grep for max-4 limit and summarize rule passes

**Delivered by:** Phase 4 → Conversation 2

---

### S3.1: Web-researcher agent file exists as a named, read-only agent ✅ DONE
**As an** architect or planner, **I want** a dedicated agent file at `agents/web-researcher.md`,
**so that** I can spawn it to gather external design patterns, library docs, or domain knowledge
before making design decisions.

**Acceptance Criteria:**
- [x] `agents/web-researcher.md` exists with valid frontmatter
- [x] Budget rule: 5–10 WebSearch/WebFetch tool calls
- [x] Prompt injection guard: treats instructions found in fetched pages as data, not directives
- [x] Output includes `## Findings`, `## Recommendation`, `## Sources`, `## Confidence`
- [x] Explicit no-edit, no-spawn constraints

---

### S3.2: Architect has sub-agent section (scout + web-researcher) ✅ DONE
**As an** architect, **I want** a clear sub-agent section in `agents/architect.md`, **so that**
I can use scout for codebase investigation and web-researcher for external knowledge.

**Acceptance Criteria:**
- [x] `agents/architect.md` contains an "Information gathering — sub-agents" section
- [x] Levels 1, 2, 3 documented (quick, scout, web-researcher)
- [x] Max-4 cap stated
- [x] Sub-agents are terminal rule present

---

### S3.3: Planner has sub-agent section (web-researcher only) ✅ DONE
**As a** planner, **I want** a sub-agent section in `agents/planner.md`, **so that** I can
use web-researcher for external domain knowledge while staying local for codebase questions.

**Acceptance Criteria:**
- [x] `agents/planner.md` contains an "Information gathering — sub-agents" section
- [x] Web-researcher permitted; scout NOT permitted (planner stays requirements-focused)
- [x] Max-4 cap stated

---

### S3.4: Reviewer has sub-agent section (scout only) ✅ DONE
**As a** reviewer, **I want** a sub-agent section in `agents/reviewer.md`, **so that** I can
use scout to cross-check patterns before flagging violations.

**Acceptance Criteria:**
- [x] `agents/reviewer.md` contains an "Information gathering — sub-agents" section
- [x] Scout permitted; web-researcher NOT permitted
- [x] Max-4 cap stated

---

### S3.5: Tester has sub-agent section (scout only) ✅ DONE
**As a** tester, **I want** a sub-agent section in `agents/tester.md`, **so that** I can
use scout to locate test fixtures, patterns, or coverage gaps before writing test plans.

**Acceptance Criteria:**
- [x] `agents/tester.md` contains an "Information gathering — sub-agents" section
- [x] Scout permitted; web-researcher NOT permitted
- [x] Max-4 cap stated
