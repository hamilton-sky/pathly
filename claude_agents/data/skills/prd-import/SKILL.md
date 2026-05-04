---
name: prd-import
description: Read any PRD file (from BMAD, hand-written, or AI-generated) and generate plan files in plans/<feature>/. Lite creates 4 required files; standard/strict create all 8 files.
argument-hint: "<feature-name> <path/to/PRD.md> [lite|standard|strict]  — e.g., hotel-search docs/hotel-search-prd.md strict"
model: opus
---

## Skill Contract

**Consumes:** Any PRD file (path provided as second argument)
**Produces:** `plans/$FEATURE/` — 4 files in lite, all 8 plan files in standard/strict, pre-populated from the PRD
**Consumed by:** `build` skill reads `CONVERSATION_PROMPTS.md` and `PROGRESS.md`

---

## Step 0: Parse Arguments

Split `$ARGUMENTS` on the first space:
- `FEATURE` = first token (the feature name, e.g., `hotel-search`)
- `PRD_PATH` = remaining tokens (the file path, e.g., `docs/hotel-search-prd.md`)
- If the final token is `lite`, `standard`, or `strict`, remove it from `PRD_PATH` and set `rigor` accordingly.
- Default: `rigor = standard`

If either is missing, stop and tell the user:
```
Usage: /prd-import <feature-name> <path/to/PRD.md>
Example: /prd-import hotel-search docs/hotel-search-prd.md
```

Check that `PRD_PATH` exists. If not, stop and report the missing file.
Check that `plans/$FEATURE/` does NOT already exist. If it does, stop and ask the user whether to overwrite.

---

## Step 1: Read the PRD

Read the full PRD file at `PRD_PATH`.

Extract these sections (they may use different headings — use best-match):
- **Feature name / title**
- **User Stories** — each story with: title, persona, goal, benefit
- **Acceptance Criteria** — per story (list items, checkboxes, or numbered)
- **Edge Cases** — per story or global
- **Out of Scope** — explicit exclusions
- **Tech stack / constraints** — any mentioned technologies, URLs, environments
- **Overview / context** — problem statement or background

If the PRD uses different section names (e.g., "Non-functional requirements", "Constraints"), map them to the closest category above.

---

## Step 2: Read Project Conventions

1. Read `CLAUDE.md` — layer structure, run commands, site list
2. Read `.claude/rules/pom-layer.md` — Locator rules, `_interact()` contract
3. Read `.claude/rules/glue-layer.md` — resolver injection contract, `register()` rules
4. Read `.claude/rules/three-layer-contract.md` — dependency direction, what belongs where
5. Identify the **target site** from the PRD (OpenLibrary, SauceDemo, phpTravels, or new)
6. Find the site's existing glue directory: `stepper/sites/<site>/pages/` — read existing action files to understand naming conventions

---

## Step 3: Plan the Conversation Split

Determine how many conversations are needed (max 4 per folder):

**Rules for splitting:**
- **Conversation 1** always covers: POM layer + glue layer (the foundation)
- **Conversation 2** covers: workflow JSON files (happy path + edge cases)
- **Conversation 3** (if needed): additional stories that depend on Conv 1 POMs
- **Conversation 4** (if needed): integration tests or exam layer additions

If complexity is LOW (1-2 stories, ≤4 ACs): 2 conversations
If complexity is MEDIUM (3-4 stories, 5-8 ACs): 3 conversations
If complexity is HIGH (5+ stories or 9+ ACs): consider splitting into two plan folders: `plans/$FEATURE-part-1/` and `plans/$FEATURE-part-2/`

---

## Step 4: Translate ACs to Verify Commands

This is the core translation step. For each acceptance criterion, determine which layer it tests and generate the appropriate verify command:

**Layer detection rules:**

| AC mentions... | Layer | Verify command type |
|---|---|---|
| "field exists", "button is visible", "locator", "selector" | POM | `grep "class.*Locator" poms/<site>/pages/<page>.py` |
| "action is registered", "workflow step runs" | Glue | `grep "resolver=resolver" stepper/sites/<site>/pages/<action>.py` |
| "navigates to", "shows results", "end-to-end", "workflow" | Workflow | `python stepper/main.py --workflow stepper/sites/<site>/workflows/<file>.json` |
| "count", "number of", "at least N" | State read | store in context and assert in workflow |
| "error message", "validation", "empty state" | Edge case workflow | separate workflow JSON file |

**Verify command format:**
```
Verify:
  <command>
  # expected: <what success looks like>
```

Always include at least one verify command per conversation that proves the deliverable is runnable, not just syntactically correct.

---

## Step 5: Map Edge Cases to Conversations

Each edge case from the PRD becomes either:

1. **A workflow file** — if it requires navigating the site to a failure state (e.g., "no results found", "invalid input")
   → Add to Conversation 2 as a separate workflow: `stepper/sites/<site>/workflows/<feature>_<edge_case>.json`

2. **A Do NOT item** — if it's a boundary ("do not implement payment flow")
   → Add to every conversation's `Do NOT` list

3. **A POM method** — if it's a state check the POM must return (e.g., "returns None when no results")
   → Add to Conversation 1 POM scope

---

## Step 6: Generate Plan Files

Create `plans/$FEATURE/`.

If `rigor = lite`, write only:
- USER_STORIES.md
- IMPLEMENTATION_PLAN.md
- PROGRESS.md
- CONVERSATION_PROMPTS.md

Merge happy flow, edge cases, architecture notes, and flow notes into those four files.

If `rigor = standard` or `strict`, write all 8 files.

If `rigor = strict`, add explicit risk, rollback, verification mapping, and approval notes.

### FILE 1: USER_STORIES.md
Read `~/.claude/templates/plan/USER_STORIES.template.md` for structure.

### FILE 2: IMPLEMENTATION_PLAN.md
Read `~/.claude/templates/plan/IMPLEMENTATION_PLAN.template.md` for structure.

### FILE 3: PROGRESS.md
Read `~/.claude/templates/plan/PROGRESS.template.md` for structure.

### FILE 4: CONVERSATION_PROMPTS.md
Read `~/.claude/templates/plan/CONVERSATION_PROMPTS.template.md` for structure.

Each conversation prompt must be self-contained, scoped to specific files and layers, include three-layer rules reminder, Do NOT list, verify command, and end with:
`After done, update plans/$FEATURE/PROGRESS.md phase X to DONE.`

### FILE 5: HAPPY_FLOW.md
Standard/strict only. Skip in lite.
Read `~/.claude/templates/plan/HAPPY_FLOW.template.md` for structure.

### FILE 6: EDGE_CASES.md
Standard/strict only. Skip in lite.
Read `~/.claude/templates/plan/EDGE_CASES.template.md` for structure.

### FILE 7: ARCHITECTURE_PROPOSAL.md
Standard/strict only. Skip in lite; merge short architecture notes into IMPLEMENTATION_PLAN.md.
Read `~/.claude/templates/plan/ARCHITECTURE_PROPOSAL.template.md` for structure.

### FILE 8: FLOW_DIAGRAM.md
Standard/strict only. Skip in lite unless the flow is unclear without a diagram.
Read `~/.claude/templates/plan/FLOW_DIAGRAM.template.md` for structure.
ASCII only. Max ~70 chars wide.

---

## Step 7: Verify Output

After writing files, confirm the selected rigor's required files exist in `plans/$FEATURE/`.

Then report:
```
PRD import complete. Created plans/$FEATURE/.

Rigor: [lite / standard / strict]

Stories imported: [count] ([story IDs])
Conversations planned: [count]
Edge case workflows: [count]

Next step: Review the plan, then run:
  /build $FEATURE        ← implement Conversation 1
  /team-flow $FEATURE    ← run the full pipeline
```

If a section was missing from the PRD, note it and leave the relevant section minimal rather than inventing content.
