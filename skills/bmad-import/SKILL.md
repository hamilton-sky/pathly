---
name: bmad-import
description: Read a BMAD PRD file and generate all 8 plan files in plans/<feature>/. Translates BMAD user stories, acceptance criteria, edge cases, and out-of-scope sections into the stepper framework pipeline format — including verify commands, Do NOT lists, and workflow conversation splits.
argument-hint: "<feature-name> <path/to/PRD.md>  — e.g., hotel-search docs/hotel-search-prd.md"
model: opus
---

## Skill Contract

**Consumes:** A BMAD PRD file (path provided as second argument)
**Produces:** `plans/$FEATURE/` — all 8 plan files, pre-populated from the BMAD PRD
**Consumed by:** `build` skill reads `CONVERSATION_PROMPTS.md` and `PROGRESS.md`

---

## Step 0: Parse Arguments

Split `$ARGUMENTS` on the first space:
- `FEATURE` = first token (the feature name, e.g., `hotel-search`)
- `PRD_PATH` = remaining tokens (the file path, e.g., `docs/hotel-search-prd.md`)

If either is missing, stop and tell the user:
```
Usage: /bmad-import <feature-name> <path/to/PRD.md>
Example: /bmad-import hotel-search docs/hotel-search-prd.md
```

Check that `PRD_PATH` exists. If not, stop and report the missing file.
Check that `plans/$FEATURE/` does NOT already exist. If it does, stop and ask the user whether to overwrite.

---

## Step 1: Read the PRD

Read the full BMAD PRD file at `PRD_PATH`.

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

## Step 6: Generate the 8 Plan Files

Create `plans/$FEATURE/` and write all 8 files.

### FILE 1: USER_STORIES.md

Read `~/.claude/templates/plan/USER_STORIES.template.md` for structure.

Populate:
- Context section: derive from PRD overview/problem statement (2 paragraphs max)
- Each BMAD user story → one Story block
- AC list: copy verbatim from PRD, format as `- [ ] AC text`
- Edge Cases: copy from PRD edge cases section for this story
- "Delivered by": fill in after determining conversation split in Step 3

---

### FILE 2: IMPLEMENTATION_PLAN.md

Read `~/.claude/templates/plan/IMPLEMENTATION_PLAN.template.md` for structure.

Populate:
- One phase per conversation
- Phase title: matches conversation title (e.g., "Phase 1 — POM + Glue Layer")
- Deliverables: list the specific files to create/modify
- Stories delivered: which story IDs this phase covers
- Verify: the verify command from Step 4

---

### FILE 3: PROGRESS.md

Read `~/.claude/templates/plan/PROGRESS.template.md` for structure.

Populate:
- Status: TODO
- All conversations: TODO
- All phases: TODO
- Story status table: all stories → TODO

---

### FILE 4: CONVERSATION_PROMPTS.md

Read `~/.claude/templates/plan/CONVERSATION_PROMPTS.template.md` for structure.

**This is the critical file.** Each conversation prompt must be:
- Self-contained (the builder can paste it without reading the plan)
- Scoped to specific files and layers only
- Include three-layer rules reminder
- Include the Do NOT list (derived from out-of-scope + layer boundaries)
- Include the verify command from Step 4
- End with: `After done, update plans/$FEATURE/PROGRESS.md phase X to DONE.`

**Conversation 1 template structure:**
```
Implement [Feature] Conversation 1 (POM + Glue Layer) from
plans/$FEATURE/IMPLEMENTATION_PLAN.md.

Stories delivered: [story IDs]

Scope:

Phase 1 — [SiteName] POM ([poms/<site>/pages/<page>.py]):
  Add Locator instances for:
    - [LOCATOR_NAME]: role="...", name="...", css="..."
    [one per interactive element from the story]
  Add methods:
    - [method_name]([params]) → [return type]

Phase 2 — Glue actions ([stepper/sites/<site>/pages/<action>.py]):
  [action_name]: builds [PageName] POM with page=page, resolver=resolver,
    reads step.params["[param]"],
    [what it does]
  Register all in register() classmethod.

Three-layer rules:
- All interactive locators must be Locator instances (pom-layer.md)
- Every POM construction must pass page=page, resolver=resolver (glue-layer.md)
- No raw page.locator() calls in glue files

Do NOT:
  [out-of-scope items from PRD]
  - Write workflow JSON (Conversation 2)
  - Hardcode URLs or credentials — read from poms/<site>/config.py

Verify:
  [verify command from Step 4]
  # expected: [success condition]

After done, update plans/$FEATURE/PROGRESS.md Phase 1 → DONE.
If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Conversation 2 template structure:**
```
Implement [Feature] Conversation 2 (Workflows) from
plans/$FEATURE/IMPLEMENTATION_PLAN.md.

Conversation 1 is DONE (POM + glue layers exist and are verified).

Scope:

Phase 1 — Happy path workflow ([stepper/sites/<site>/workflows/<feature>.json]):
  Steps: [action sequence from story happy path]
  Params: [concrete param values for the happy path]

[One Phase per edge case workflow:]
Phase N — [Edge case name] ([stepper/sites/<site>/workflows/<feature>_<edge_case>.json]):
  Steps: [action sequence that reaches the edge case state]
  Assert: [what the workflow should verify]

Do NOT:
  - Add new POM methods (Conversation 1 is locked)
  - Add selectors to workflow JSON files
  [out-of-scope items]

Verify:
  python stepper/main.py --workflow stepper/sites/<site>/workflows/<feature>.json
  # expected: passes end-to-end

After done, update plans/$FEATURE/PROGRESS.md Phase 2 → DONE, Status → DONE.
```

---

### FILE 5: HAPPY_FLOW.md

Read `~/.claude/templates/plan/HAPPY_FLOW.template.md` for structure.

Derive the happy path from the PRD's main user story (the primary persona completing the primary goal successfully). List as numbered steps.

---

### FILE 6: EDGE_CASES.md

Read `~/.claude/templates/plan/EDGE_CASES.template.md` for structure.

One section per edge case from the PRD. For each:
- Description
- How it is handled (which layer catches it)
- Which workflow file covers it (set in Conversation 2)

---

### FILE 7: ARCHITECTURE_PROPOSAL.md

Read `~/.claude/templates/plan/ARCHITECTURE_PROPOSAL.template.md` for structure.

Derive from PRD tech stack + project conventions:
- Which site this targets
- Which POM files are new vs modified
- Which glue files are new vs modified
- Dependency direction confirmation (Flow → Glue → POM)
- Any new Locator fields needed

---

### FILE 8: FLOW_DIAGRAM.md

Read `~/.claude/templates/plan/FLOW_DIAGRAM.template.md` for structure.

ASCII only. Show:
- The happy path as a vertical flow through layers
- Label each arrow with the action name or method name
- Show the resolver cascade entry point (glue → POM → resolver)
- Max ~70 chars wide

---

## Step 7: Verify Output

After writing all 8 files, run:
```
ls plans/$FEATURE/ | wc -l
# expected: 8
```

Then report to the user:
```
BMAD import complete. Created plans/$FEATURE/ with 8 files.

Stories imported: [count] ([story IDs])
Conversations planned: [count]
Edge case workflows: [count]

Next step: Review the plan, then run:
  /build $FEATURE        ← implement Conversation 1
  /team-flow $FEATURE    ← run the full pipeline
```

If a section was missing from the PRD (e.g., no edge cases listed), note it in the report and leave the relevant section minimal rather than inventing content.
