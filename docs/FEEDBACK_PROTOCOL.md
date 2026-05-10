# Feedback File Protocol

Feedback files are Pathly's control-plane signals. They live under
`plans/<feature>/feedback/`.

File present means issue open. File deleted means resolved.

## Files

| File | Written by | Resolved by | Purpose |
|---|---|---|---|
| `ARCH_FEEDBACK.md` | reviewer or tester | architect | Structural or design problem blocks implementation. |
| `REVIEW_FAILURES.md` | reviewer | builder | Implementation problem that can be fixed without redesign. |
| `TEST_FAILURES.md` | tester | builder | Acceptance criteria fail or lack coverage. |
| `IMPL_QUESTIONS.md` | builder | planner | Requirement ambiguity: what should this do? |
| `DESIGN_QUESTIONS.md` | builder | architect | Technical blocker: how should this be built safely? |
| `HUMAN_QUESTIONS.md` | any role or orchestrator | user | Product/business decision, stall, or unresolved loop. |

## Frontmatter

Each agent should inject YAML frontmatter into feedback files when creating them:

```yaml
---
created_at: 2026-05-04T08:12:00Z
created_by_event: <last-event-timestamp-or-id>
ttl_hours: 24
---
```

`verify-state`, `doctor`, and startup checks can use this metadata to flag stale
or orphaned feedback files. If hooks are not installed, feedback files still
work; they simply do not carry TTL metadata.

## Routing

```text
ARCH_FEEDBACK.md    -> architect
DESIGN_QUESTIONS.md -> architect
IMPL_QUESTIONS.md   -> planner
REVIEW_FAILURES.md  -> builder
TEST_FAILURES.md    -> builder
HUMAN_QUESTIONS.md  -> user
```

When multiple files exist, the FSM routes one at a time using the priority
documented in [ORCHESTRATOR_FSM.md](ORCHESTRATOR_FSM.md).

## Question Tags

Builder questions should be tagged:

- `[REQ]` for requirement ambiguity, routed to planner.
- `[ARCH]` for technical/design blockers, routed to architect.
- `[UNSURE]` when ownership is unclear; write both question files and let the
  correct owner discard what is not theirs.

A classify-feedback hook can classify and split `IMPL_QUESTIONS.md` when
`ANTHROPIC_API_KEY` is available. It exits silently when unavailable so hooks
stay optional.

## Auto-Fix Review Findings

The reviewer may mark trivial findings as `[AUTO_FIX]` in
`REVIEW_FAILURES.md`. The builder applies those patches first, then handles any
regular violations. If an auto-fix patch does not apply cleanly, treat it as a
normal review failure.

## Resolution Rules

1. The owner fixes or answers the issue.
2. The owner deletes the feedback file.
3. The orchestrator sees no open feedback and resumes the previous state.
4. Max retry cycles are enforced per conversation and feedback file.
5. Zero-diff review loops escalate to `HUMAN_QUESTIONS.md [STALL]`.

Feedback files are blocking. Pathly should not advance a workflow while any
known feedback file remains open.
