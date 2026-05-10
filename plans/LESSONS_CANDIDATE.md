# Lessons Candidate

---

## [pathly-two-project-split] Storm must visualize file structure changes

### Pattern
When a feature reorganizes the file system, the storm session left the proposed structure implicit — it was only visible at implementation time.

### Rule
MUST show an ASCII directory tree of the before/after layout in the storm session whenever the feature involves structural changes to the repo.

### Injection
- Add to storm skill: "If the feature changes directory structure, draw an ASCII tree showing before and after before moving to planning."

### Source
Feature: pathly-two-project-split | Stage: planning | Date: 2026-05-10

---

## [pathly-two-project-split] Conversations should be tasks, not milestones

### Pattern
Each "conversation" covered too much ground — closer to a milestone than a single-scope task. This made scope cuts necessary mid-conversation.

### Rule
MUST break conversations into single-scope tasks, each with one clear verify command and a file list small enough to complete without scope cuts.

### Injection
- Add to CONVERSATION_PROMPTS.md template: each entry should cover one cohesive change, not a phase.
- Add to planner instructions: if a conversation touches more than 5 files, split it.

### Source
Feature: pathly-two-project-split | Stage: planning | Date: 2026-05-10

---

## [pathly-two-project-split] Plan templates need cross-referencing story IDs

### Pattern
USER_STORIES.md, IMPLEMENTATION_PLAN.md, and CONVERSATION_PROMPTS.md were standalone — no story ID traced end-to-end through the plan files.

### Rule
MUST include story IDs (e.g. S1.1) in every plan file so a story can be traced from user need through implementation task to verify command.

### Injection
- Add story ID column to CONVERSATION_PROMPTS.md template.
- Add story ID references to IMPLEMENTATION_PLAN.md phase rows.

### Source
Feature: pathly-two-project-split | Stage: planning | Date: 2026-05-10

---

## [pathly-two-project-split] Add routing README to every plan folder

### Pattern
Agents had to infer which plan files were relevant to their role by reading all of them.

### Rule
MUST create plans/<feature>/README.md listing which files each agent role should read (PO, architect, builder, reviewer).

### Injection
- Add to plan creation: generate plans/<feature>/README.md with a role → files table as the first file written.

### Source
Feature: pathly-two-project-split | Stage: planning | Date: 2026-05-10
