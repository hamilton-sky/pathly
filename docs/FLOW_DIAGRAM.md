# Pathly Flow Diagram

Pathly has three public front doors over the same core workflows:

- Claude Code slash skills: `/pathly ...` and `/path ...`
- Codex plugin skills: `Use Pathly ...`
- CLI fallback: `pathly ...`

## High-Level Flow

```text
plain-English request
  |
  v
director / pathly router
  |
  |-- help            -> state-aware numbered menu
  |-- doctor          -> local prerequisite and stuck-state diagnostics
  |-- explore         -> read-only codebase investigation
  |-- debug           -> bug investigation workflow
  |-- review          -> review current changes
  |-- meet            -> read-only role consultation note
  `-- flow / run      -> feature pipeline
```

## Feature Pipeline

```text
flow <feature>
  |
  v
startup checks
  |
  v
discovery choice
  |-- storm first
  |-- skip discovery
  `-- import PRD / BMAD PRD
  |
  v
plan
  |-- lite: 4 core files
  |-- standard: 8 plan files
  `-- strict: 8 plan files + audit state requirements
  |
  v
rigor escalator
  |
  v
build one conversation
  |
  v
review
  |-- REVIEW_FAILURES.md -> builder
  |-- ARCH_FEEDBACK.md -> architect
  `-- pass -> next conversation or test
  |
  v
test
  |-- TEST_FAILURES.md -> builder
  `-- pass -> retro
  |
  v
retro / lessons / optional archive
```

## Files Written By A Feature

```text
plans/<feature>/
|-- USER_STORIES.md
|-- IMPLEMENTATION_PLAN.md
|-- PROGRESS.md
|-- CONVERSATION_PROMPTS.md
|-- HAPPY_FLOW.md                 # standard/strict or escalator-added
|-- EDGE_CASES.md                 # standard/strict or escalator-added
|-- ARCHITECTURE_PROPOSAL.md      # standard/strict or escalator-added
|-- FLOW_DIAGRAM.md               # standard/strict or escalator-added
|-- STATE.json                    # runtime checkpoint when driver runs
|-- EVENTS.jsonl                  # append-only event log when driver runs
|-- consults/                     # meet notes
`-- feedback/
    |-- ARCH_FEEDBACK.md
    |-- REVIEW_FAILURES.md
    |-- IMPL_QUESTIONS.md
    |-- DESIGN_QUESTIONS.md
    |-- TEST_FAILURES.md
    `-- HUMAN_QUESTIONS.md
```

`lite` always creates the four core plan files. Extra planning files can be
added by explicit rigor or by the escalator when the workflow discovers risk.

## Feedback Routing

```text
reviewer -> ARCH_FEEDBACK.md    -> architect
reviewer -> REVIEW_FAILURES.md  -> builder
builder  -> IMPL_QUESTIONS.md   -> planner
builder  -> DESIGN_QUESTIONS.md -> architect
tester   -> TEST_FAILURES.md    -> builder
any role -> HUMAN_QUESTIONS.md  -> user
```

File exists means open. Deleting the file means resolved. The FSM must not move
forward while a known feedback file exists.

## Invocation Examples

Claude Code:

```text
/pathly add password reset
/pathly flow checkout-flow
/pathly debug checkout button does nothing
/pathly meet checkout-flow
```

Codex:

```text
Use Pathly help
Use Pathly flow for checkout-flow
Use Pathly to explore how checkout state flows
```

CLI:

```text
pathly help
pathly init checkout-flow
pathly flow checkout-flow --entry build
pathly meet checkout-flow --role planner --question "Is this split too large?"
```
