# Orchestrator FSM

The orchestrator is a finite state machine over the filesystem.

It does not depend on hidden conversation memory or agent intuition. Every step is:

1. Read disk.
2. Derive the current state.
3. Apply one event.
4. Write state and event logs.
5. Emit exactly one next action.

## Files

Each feature stores workflow state beside the plan:

```text
plans/<feature>/
|-- STATE.json
|-- EVENTS.jsonl
|-- PROGRESS.md
`-- feedback/
    |-- ARCH_FEEDBACK.md
    |-- REVIEW_FAILURES.md
    |-- IMPL_QUESTIONS.md
    |-- DESIGN_QUESTIONS.md
    |-- TEST_FAILURES.md
    `-- HUMAN_QUESTIONS.md
```

`STATE.json` is a cache and checkpoint. Disk recovery wins if `STATE.json` disagrees with feedback files or `PROGRESS.md`.

`EVENTS.jsonl` is append-only. Each line records an event, previous state, next state, selected action, and timestamp.

## States

```ts
type State =
  | "IDLE"
  | "STORMING"
  | "STORM_PAUSED"
  | "PLANNING"
  | "PLAN_PAUSED"
  | "BUILDING"
  | "REVIEWING"
  | "IMPLEMENT_PAUSED"
  | "TESTING"
  | "TEST_PAUSED"
  | "RETRO"
  | "BLOCKED_ON_FEEDBACK"
  | "BLOCKED_ON_HUMAN"
  | "DONE"
```

## Events

```ts
type Event =
  | { type: "COMMAND"; value: string }
  | { type: "AGENT_DONE"; agent: AgentName }
  | { type: "FILE_CREATED"; file: FeedbackFile }
  | { type: "FILE_DELETED"; file: FeedbackFile }
  | { type: "HUMAN_RESPONSE"; value: string }
  | { type: "NO_DIFF_DETECTED" }
  | { type: "IMPLEMENT_COMPLETE" }
  | { type: "STATE_TRANSITION"; from_state: State; to_state: State }
  | { type: "SYSTEM_EVENT"; action: "RETRY" | "ERROR" | "TIMEOUT"; metadata: { retry_key?: string } }
```

Only known feedback files under `plans/<feature>/feedback/` count as feedback events.

## Context

```ts
interface Context {
  feature: string
  mode: "interactive" | "fast"
  rigor: "lite" | "standard" | "strict"
  currentConversation?: number
  retryCountByKey: Record<string, number>
  previousState?: State
  activeFeedbackFile?: FeedbackFile
  activeTarget?: AgentName | "human"
  lastActor?: AgentName
}
```

`mode` controls human pauses. `rigor` controls how much workflow structure is required.

Retry keys should include the current conversation and feedback file, for example `conv-2:REVIEW_FAILURES.md`. This prevents unrelated feedback loops from consuming each other's retry budget.

## Rigor Modes

`standard` is the default and preserves the current workflow.

| Rigor | Use for | Required plan files | Gates |
|---|---|---|---|
| `lite` | small, low-risk changes | `USER_STORIES.md`, `IMPLEMENTATION_PLAN.md`, `PROGRESS.md`, `CONVERSATION_PROMPTS.md` | plan -> build -> optional review/test |
| `standard` | normal product features | all 8 plan files | build + review per conversation, test, retro |
| `strict` | auth, payments, data loss, migrations, regulated work | all 8 plan files plus mandatory `STATE.json` and `EVENTS.jsonl` | all standard gates plus mandatory human approvals and audit logs |

`lite` reduces plan surface area but keeps the files needed by `/build`.

`standard` is the current pipeline: storm can be skipped, human pauses are default, feedback routing is enforced, and `STATE.json` / `EVENTS.jsonl` are written when runtime support exists.

`strict` is audit-grade workflow. It requires discovery or PRD import before planning, requires human approval at storm, plan, implementation, and test gates, requires review after every conversation, requires complete acceptance-criteria test mapping, and treats missing `STATE.json` or `EVENTS.jsonl` as a workflow error. `strict` should reject `fast` unless a future project explicitly opts into strict automation.

## Feedback Priority

When multiple feedback files exist, route exactly one target at a time:

1. `HUMAN_QUESTIONS.md` -> human
2. `ARCH_FEEDBACK.md` -> architect
3. `DESIGN_QUESTIONS.md` -> architect
4. `IMPL_QUESTIONS.md` -> planner
5. `REVIEW_FAILURES.md` -> builder
6. `TEST_FAILURES.md` -> builder

`ARCH_FEEDBACK.md` blocks all builder work until resolved. `DESIGN_QUESTIONS.md` also routes to architect before planner clarification, because implementation cannot continue while the design is impossible.

## Global Guards

These guards run before normal transitions:

```ts
if (feedback.HUMAN_QUESTIONS) {
  return BLOCKED_ON_HUMAN
}

if (feedback.anyOpen) {
  return BLOCKED_ON_FEEDBACK
}

if (progress.allConversationsDone && state === "IMPLEMENT_PAUSED") {
  emit({ type: "IMPLEMENT_COMPLETE" })
}
```

No forward progress is allowed while any known feedback file exists.

Only one agent may be active at a time.

## Core Transitions

```text
IDLE + COMMAND("/team-flow <feature>")
-> STORMING
-> spawn(architect)

STORMING + AGENT_DONE(architect)
-> STORM_PAUSED

STORM_PAUSED + HUMAN_RESPONSE("yes")
-> PLANNING
-> spawn(planner)

STORM_PAUSED + HUMAN_RESPONSE("no")
-> DONE

PLANNING + AGENT_DONE(planner)
-> PLAN_PAUSED

PLAN_PAUSED + HUMAN_RESPONSE("go")
-> BUILDING
-> spawn(builder)

PLAN_PAUSED + HUMAN_RESPONSE("stop")
-> DONE

BUILDING + AGENT_DONE(builder)
-> REVIEWING
-> spawn(reviewer)

REVIEWING + FILE_CREATED(ARCH_FEEDBACK.md)
-> BLOCKED_ON_FEEDBACK
-> spawn(architect)

REVIEWING + FILE_CREATED(REVIEW_FAILURES.md)
-> BLOCKED_ON_FEEDBACK
-> spawn(builder)

REVIEWING + AGENT_DONE(reviewer)
-> IMPLEMENT_PAUSED

IMPLEMENT_PAUSED + HUMAN_RESPONSE("continue")
-> BUILDING
-> spawn(builder)

IMPLEMENT_PAUSED + IMPLEMENT_COMPLETE
-> TESTING
-> spawn(tester)

IMPLEMENT_PAUSED + HUMAN_RESPONSE("stop")
-> DONE

TESTING + FILE_CREATED(TEST_FAILURES.md)
-> BLOCKED_ON_FEEDBACK
-> spawn(builder)

TESTING + AGENT_DONE(tester)
-> TEST_PAUSED

TEST_PAUSED + HUMAN_RESPONSE("fix")
-> BUILDING
-> spawn(builder)

TEST_PAUSED + HUMAN_RESPONSE("done")
-> RETRO
-> spawn(quick)

RETRO + AGENT_DONE(quick)
-> DONE
```

Fast mode applies the same transitions, but auto-emits the affirmative human responses at pause states. `strict` mode does not auto-emit human approvals.

## Feedback Loop

Entering `BLOCKED_ON_FEEDBACK` selects the highest-priority open feedback file and increments its retry key, except for `HUMAN_QUESTIONS.md` and zero-diff escalation.

```text
BLOCKED_ON_FEEDBACK + FILE_DELETED(activeFeedbackFile)
-> previous logical state
```

If a retry key exceeds 2:

```text
BLOCKED_ON_FEEDBACK
-> BLOCKED_ON_HUMAN
-> write HUMAN_QUESTIONS.md
```

If builder finishes a `REVIEW_FAILURES.md` resolution and no implementation diff exists:

```text
BLOCKED_ON_FEEDBACK + AGENT_DONE(builder) + NO_DIFF_DETECTED
-> BLOCKED_ON_HUMAN
-> write HUMAN_QUESTIONS.md
```

## Recovery

`orchestrator --recover <feature>` must reconstruct state by reading:

- `plans/<feature>/feedback/*.md`
- `plans/<feature>/PROGRESS.md`
- `plans/<feature>/STATE.json`
- `plans/<feature>/EVENTS.jsonl`

Recovery order:

1. If `HUMAN_QUESTIONS.md` exists, state is `BLOCKED_ON_HUMAN`.
2. If any feedback file exists, state is `BLOCKED_ON_FEEDBACK`.
3. If all conversations are done and tests have not passed, state is `TESTING` or `TEST_PAUSED` based on the latest event.
4. If any conversation is TODO, state is `BUILDING` or `IMPLEMENT_PAUSED` based on the latest event.
5. If plan files exist but no build started, state is `PLAN_PAUSED`.
6. If only storm output exists, state is `STORM_PAUSED`.
7. Otherwise state is `IDLE`.

## Observability

Every transition should produce logs like:

```text
[EVENT] AGENT_DONE(builder)
[STATE] BUILDING -> REVIEWING
[ACTION] spawn(reviewer)
[FILE] REVIEW_FAILURES.md created
[STATE] REVIEWING -> BLOCKED_ON_FEEDBACK
[ACTION] spawn(builder)
```

The event log is the audit trail. The state file is the checkpoint. The filesystem is the source of truth.
