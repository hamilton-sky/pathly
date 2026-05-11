# Philosophy - Why Pathly Works This Way

Pathly is built around a small set of design choices that should stay stable
across CLI, Claude Code, Codex, and future adapters.

## 1. Files Are The Protocol

Pathly does not rely on hidden conversation memory as the workflow state. Agents
write files, the orchestrator reads files, and the next action is derived from
disk.

Useful state is visible in:

```text
plans/<feature>/
|-- PROGRESS.md
|-- STATE.json
|-- EVENTS.jsonl
|-- feedback/
`-- consults/
```

This makes interruption and recovery practical. If a session stops, another
agent can inspect the filesystem and continue.

## 2. Agents Are Contracts

An agent is a responsibility boundary, not a persona. The role contract defines
what the agent may decide, write, and never do.

Examples:

- Reviewer reports findings; it does not patch source.
- Builder implements scoped work; it does not silently redesign architecture.
- Orchestrator routes state; it does not implement features.
- PO is optional and clarifies product intent when needed.

## 3. Feedback Loops Beat Linear Pipelines

A straight pipeline cannot recover well when the wrong role needs to answer a
problem. Pathly routes problems through typed feedback files:

```text
reviewer -> ARCH_FEEDBACK.md    -> architect
reviewer -> REVIEW_FAILURES.md  -> builder
builder  -> IMPL_QUESTIONS.md   -> planner
builder  -> DESIGN_QUESTIONS.md -> architect
tester   -> TEST_FAILURES.md    -> builder
any role -> HUMAN_QUESTIONS.md  -> user
```

File present means open. File deleted means resolved.

## 4. Human Gates Are Intentional

The default workflow pauses at meaningful stage transitions so wrong assumptions
can be caught before more work is built on top of them.

Fast mode skips allowed pauses, but it does not skip feedback files, retry
limits, missing prerequisites, or strict approval gates.

## 5. Rigor And Speed Are Separate

Rigor controls how much process a feature needs:

- `nano`: tiny, low-risk changes
- `lite`: default path with the four core plan files
- `standard`: all eight plan files and normal review/test gates
- `strict`: audit-grade workflow with explicit approvals

Speed controls whether pauses are interactive or auto-advanced. Keep those
concepts separate in docs, prompts, and code.

## 6. Lessons Improve Plans, Not Agent Personalities

Retrospectives and lessons should become planning constraints. The goal is not
to make an agent vaguely "smarter"; the goal is to make future plans harder to
fail in the same way.

## 7. Core Is Host-Neutral

Shared workflow meaning belongs in `core/`. Claude Code slash syntax, Codex
natural-language invocation, direct `.agents/skills/` discovery, and terminal
commands are adapter concerns.
