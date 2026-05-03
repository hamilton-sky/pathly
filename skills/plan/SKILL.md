---
name: plan
description: Plan a new feature by creating a plans folder with 8 files: USER_STORIES.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, CONVERSATION_PROMPTS.md (max 4 conversations per folder), HAPPY_FLOW.md, EDGE_CASES.md, ARCHITECTURE_PROPOSAL.md, and FLOW_DIAGRAM.md.
argument-hint: "[feature-name, e.g., add-saucedemo-checkout, new-resolver-strategy]"
model: opus
---

## Skill Contract

**Consumes (optional):** `plans/STORM_SEED.md` — pre-filled answers for Step 1 interview
**Produces:** `plans/$ARGUMENTS/` — 8 plan files
**Consumed by:** `build` skill reads `plans/$ARGUMENTS/CONVERSATION_PROMPTS.md` and `PROGRESS.md`

## Step 1: Understand the feature

Check if `plans/STORM_SEED.md` exists.

**If it exists:** Read it, pre-fill interview answers (Decisions Made → architecture decisions, Constraints → scope limits, Open Questions → unknowns), confirm with user, then delete the seed file.

**If it does not exist:** Interview the user — What does it do? Which layers does it touch? Dependencies? Complexity (Small/Medium/Large)? Skip if user already gave a detailed description.

## Step 2: Research the codebase

1. Read CLAUDE.md and linked rules files — layer structure, dependency direction, naming conventions
2. Find similar existing components — use as reference patterns
3. Identify files to create or modify
4. Check test directory conventions if tests are in scope

## Step 3: Create the plans folder

Create `plans/$ARGUMENTS/` with **8 files**.

> **Conversation cap rule**: Max 4 conversations per folder. If more needed, split into `plans/$ARGUMENTS-part-1/` (foundation) and `plans/$ARGUMENTS-part-2/` (depends on part-1 DONE).

### 3a. USER_STORIES.md
Read ~/.claude/templates/plan/USER_STORIES.template.md for the exact file structure.

### 3b. IMPLEMENTATION_PLAN.md
Read ~/.claude/templates/plan/IMPLEMENTATION_PLAN.template.md for the exact file structure.

### 3c. PROGRESS.md
Read ~/.claude/templates/plan/PROGRESS.template.md for the exact file structure.

### 3d. CONVERSATION_PROMPTS.md
Key file — verbatim copy-paste prompts for each conversation. Max 4 conversations per folder.
Read ~/.claude/templates/plan/CONVERSATION_PROMPTS.template.md for the exact file structure.

### 3e. HAPPY_FLOW.md
Read ~/.claude/templates/plan/HAPPY_FLOW.template.md for the exact file structure.

### 3f. EDGE_CASES.md
Read ~/.claude/templates/plan/EDGE_CASES.template.md for the exact file structure.

### 3g. ARCHITECTURE_PROPOSAL.md
Read ~/.claude/templates/plan/ARCHITECTURE_PROPOSAL.template.md for the exact file structure.

### 3h. FLOW_DIAGRAM.md
ASCII only (`[]`, `──►`, `├─`, `└─`, `│`). Show only layers touched. Include happy path + resolver fallback. Label arrows with action name or cfg key. Max ~70 chars wide.
Read ~/.claude/templates/plan/FLOW_DIAGRAM.template.md for the exact file structure.

---

## Conversation Splitting Rules

1. Each conversation must leave the codebase runnable — end every prompt with a verify command.
2. Hard cap: 4 conversations per folder. If more needed, create part-2 folder.
3. Natural seams: POM layer first → Glue layer → Flow + integration test → Engine changes (own conversation).
4. Every prompt must say "Do NOT touch [X] yet."
5. Later prompts reference: "Conversations 1-N are DONE (description)."
6. Target 3-6 phases per conversation.
7. Each prompt is self-contained — references IMPLEMENTATION_PLAN.md but runnable without it.

## Team-Safe Prompt Rules

1. NEVER reference specific line numbers — use class/method names.
2. NEVER reference exact test counts — use relative language ("all existing exam tests").
3. Always include the three-layer checklist in prompts that touch glue or POM.
4. Include a recovery instruction: "If verification fails and the fix requires out-of-scope changes, stop and report. If fundamentally broken, rollback with git checkout on affected files and retry."

## Step 4: Verify structure

- All 8 files exist in `plans/$ARGUMENTS/`
- CONVERSATION_PROMPTS.md has ≤4 conversations
- Conversation prompts reference correct phase numbers
- PROGRESS.md conversation table matches CONVERSATION_PROMPTS.md
- Phase numbers consistent across all files
- Verify commands use correct workflow path or pytest command

## Step 5: Report

```
## Plans folder created: plans/$ARGUMENTS/

Files:
- USER_STORIES.md — N stories with acceptance criteria
- IMPLEMENTATION_PLAN.md — N phases across N conversations
- PROGRESS.md — Tracking table (all TODO)
- CONVERSATION_PROMPTS.md — N conversation prompts ready to paste (max 4)
- HAPPY_FLOW.md — Ideal automation journey
- EDGE_CASES.md — N edge cases documented
- ARCHITECTURE_PROPOSAL.md — Design decisions
- FLOW_DIAGRAM.md — ASCII flow diagram (happy path + fallback)

Seed consumed: [yes — plans/STORM_SEED.md was read and deleted / no — no seed file found]
Next: /build $ARGUMENTS
```
