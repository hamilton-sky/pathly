# Scout Delegation — User Stories

## Context

The builder agent currently has two options when it needs codebase context mid-task: use the
`quick` agent (max 2 tool calls, 1-line answer) or write a feedback file. There is no middle tier
for investigations that require reading 3–15 files across multiple directories before implementation
begins. This gap leads to either shallow context (over-use of quick) or unnecessary round-trips
(feedback files for questions the builder could answer itself with a focused read-only search).

The scout agent fills this gap: a read-only subagent that builder spawns (up to three, in parallel)
before starting any edits. Scout gathers structured findings; builder compresses them into a summary
before touching files. Scouts are builder-internal — invisible to the orchestrator FSM.

## Stories

### Story 1.1: Scout agent file exists as a named, read-only agent
**As a** builder, **I want** a dedicated agent file at `agents/scout.md`, **so that** I can spawn
it via the Agent tool with `subagent_type="scout"` and `model=haiku` to investigate codebase
structure without modifying any file.

**Acceptance Criteria:**
- [ ] `agents/scout.md` exists with valid frontmatter (name, role, model fields)
- [ ] The file contains explicit language forbidding file edits, feedback file creation, and spawning further agents
- [ ] The file defines a Structured Findings output format that builder can parse
- [ ] The file includes the Quick vs Scout decision table

**Edge Cases:**
- Scout receives a question answerable in 1 tool call — scout still answers, builder learns to use quick next time
- Scout surfaces ambiguity — scout does NOT write a feedback file; it flags in findings; builder writes the file

**Delivered by:** Phase 1 → Conversation 1

---

### Story 1.2: Builder knows when to use scout vs quick
**As a** builder, **I want** a clear Quick vs Scout decision rule in `agents/builder.md` with an
example table, **so that** I reach for the right tool without rereading agent definitions each time.

**Acceptance Criteria:**
- [ ] `agents/builder.md` contains a "Scout delegation" section
- [ ] The section includes the Quick vs Scout decision table (Typical tool calls, Output shape, Lifetime, Example questions)
- [ ] The section includes the max-3-scouts-per-conversation limit
- [ ] The section includes the summarize-before-editing rule, marked as load-bearing

**Edge Cases:**
- Builder tempted to spawn 4 scouts — the 3-scout cap is documented; builder must batch or discard the fourth question
- Builder skips the summary step — this violates the load-bearing rule; the rule must be prominent enough that a future reviewer would catch it

**Delivered by:** Phase 2 → Conversation 1

---

### Story 2.1: Build skill documents scout constraints
**As a** builder reading `skills/build/SKILL.md`, **I want** a scout delegation section that
restates the max-3 cap and summarize-before-editing rule, **so that** these norms are impossible
to miss even without reading `agents/builder.md`.

**Acceptance Criteria:**
- [ ] `skills/build/SKILL.md` contains a "Scout delegation" or equivalent section
- [ ] The section states the max-3-scouts limit
- [ ] The section states that builder must compress scout findings into a summary before making any edits
- [ ] The section states that scouts are read-only and cannot create feedback files

**Edge Cases:**
- SKILL.md and builder.md diverge over time — both files are kept minimal so drift is obvious

**Delivered by:** Phase 3 → Conversation 2

---

### Story 2.2: Static assertions verify all three files
**As a** framework maintainer, **I want** grep assertions that confirm the three load-bearing rules
are present in the right files, **so that** a future edit that accidentally removes a key constraint
is caught immediately.

**Acceptance Criteria:**
- [ ] `agents/scout.md` grep for explicit no-edit language passes
- [ ] `agents/builder.md` grep for builder as sole implementation owner passes
- [ ] `skills/build/SKILL.md` grep for max-3-scouts limit and summarize rule passes

**Edge Cases:**
- A refactor renames the section header — grep targets content keywords, not headers

**Delivered by:** Phase 4 → Conversation 2
