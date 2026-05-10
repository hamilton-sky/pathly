# pathly-two-project-split — Retrospective

## Plan Quality

**Conversation sizing:** Conversations were too coarse — each one was closer to a milestone than a task. Should be broken into smaller, single-scope tasks with explicit verify commands so scope cuts don't happen mid-conversation.

**Surprises:** None. Implementation went cleanly across all 4 conversations.

**Missing from plan:** When storming a feature that changes file structure, the storm session should show the proposed directory layout as an ASCII tree in chat — not leave it implicit. The structural change was the whole point of this feature and it wasn't visualized until implementation.

## What Worked

- Clean 4-conversation sequencing: restructure → installer → engine CLI → docs
- No cross-import violations introduced
- Test-first per conversation kept verification honest
- Stale monolith directories (`pathly/`, `orchestrator/`) caught and cleaned up before docs were written

## What to Improve Next Time

- **Break conversations into tasks.** "Conversation" is too large a unit. Use explicit tasks with single-scope verify commands instead.
- **Cross-reference templates.** USER_STORIES.md story IDs should trace through IMPLEMENTATION_PLAN.md into CONVERSATION_PROMPTS.md verify commands. Right now each file is standalone.
- **User stories are for PO/planner, not builder.** Builder should receive IMPLEMENTATION_PLAN + CONVERSATION_PROMPTS only. User stories inform the plan; they are not implementation instructions.
- **Add a routing README.** `plans/<feature>/README.md` should tell each agent which files are relevant to their role — PO reads X, architect reads Y, builder reads Z, reviewer reads W.
- **Visualize file structure in storm.** Any storm session that proposes structural changes must show an ASCII tree of the before/after layout in chat before planning begins.

## Seed for Next Storm

> pathly-two-project-split is complete. The two-package split (`pathly-adapters` / `pathly-engine`) is working and tested. Key process improvements identified: storm sessions must show file structure changes as ASCII trees; plan templates need cross-referencing story IDs; conversations should be broken into smaller single-scope tasks; and a routing README should be added to each plan folder to direct agents to the right files.
