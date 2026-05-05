# team-flow - Feature Pipeline

Run the Pathly feature pipeline with filesystem state, plan files, and feedback
loops.

## Core Flow

```text
discover -> plan -> build -> review -> fix? -> test -> fix? -> retro
```

## Rigor

- `nano`: direct small fix, no plan files, limited scope.
- `lite`: four core plan files and lighter gates.
- `standard`: full planning and review/test gates.
- `strict`: audit-friendly state, approvals, rollback thinking, and mandatory
  human gates.

## State

Workflow state is stored in project files:

```text
plans/<feature>/
  USER_STORIES.md
  IMPLEMENTATION_PLAN.md
  PROGRESS.md
  CONVERSATION_PROMPTS.md
  feedback/
  STATE.json
  EVENTS.jsonl
```

Open feedback files block the pipeline. Deleting a feedback file means the issue
has been resolved.
