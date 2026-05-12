# Production Readiness Hardening — Feature Index

> **Read this first.** Every agent working on this feature should load this file before any other plan file.
> It maps every file in this folder so you can fetch only what you need in one read.

---

## Plan files

| File | Written by | Read by | Purpose |
|---|---|---|---|
| `FEATURE_INDEX.md` | Planner | All agents | This file — single entry point for feature context |
| `USER_STORIES.md` | Planner | Tester, Reviewer | Acceptance criteria — the contract |
| `IMPLEMENTATION_PLAN.md` | Planner | Builder, Architect | Phase-by-phase design — the what and how |
| `CONVERSATION_PROMPTS.md` | Planner | Builder | Exact builder prompts — one section per conversation |
| `PROGRESS.md` | Builder, Orchestrator | Orchestrator, Builder | Conversation status — the checkpoint |

### Optional plan files (present if signals fired)

| File | Present? | Purpose |
|---|---|---|
| `ARCHITECTURE_PROPOSAL.md` | no | Cross-layer design decisions |
| `EDGE_CASES.md` | no | Failure modes and risk scenarios |
| `HAPPY_FLOW.md` | no | Golden-path narrative |
| `FLOW_DIAGRAM.md` | no | Multi-component interaction diagram |

---

## Codebase touchpoints

Files in the live repo that this feature reads or modifies.

| Codebase file | Conversation | What changes |
|---|---|---|
| `pathly-engine/orchestrator/reducer.py` | Conv 1 | Validate COMMAND metadata enums; guard `_AGENT_TRANSITIONS` lookup → soft-escalate invalid pairs |
| `pathly-engine/runners/claude.py` | Conv 1 | Validate and clamp `CLAUDE_AGENT_TIMEOUT` env var; warn to stderr if clamped |
| `pathly-engine/runners/codex.py` | Conv 1 | Validate and clamp `PATHLY_RUNNER_TIMEOUT` env var; warn to stderr if clamped |
| `pathly-engine/team_flow/manager.py` | Conv 2 | Thread-based `input()` timeout; check `run_claude()` return code in feedback loop; replace `sys.exit(1)` on git failure with `SystemEvent(action="ERROR")`; add PID lockfile |
| `pathly-engine/tests/test_fsm.py` | Conv 3 | New tests: invalid reducer transitions, unrecognized event type, metadata validation |
| `pathly-engine/tests/test_runners.py` | Conv 3 | New tests: timeout clamp (0, negative, non-numeric, above max) |
| `pathly-engine/tests/test_team_flow_smoke.py` | Conv 3 | New tests: feedback loop agent failure, git failure recovery, lockfile startup check |

> **Verify these paths exist before editing.** Glob each one. If a path is wrong, correct it before proceeding.

---

## Conversation map

| Conv | Title | Stories | Status | Key files touched |
|---|---|---|---|---|
| 1 | Reducer + runner hardening | S1, S2 | TODO | `reducer.py`, `runners/claude.py`, `runners/codex.py` |
| 2 | Manager hardening | S3, S4, S5, S6 | TODO | `team_flow/manager.py` |
| 3 | Tests for all gaps | S1–S6 | TODO | `test_fsm.py`, `test_runners.py`, `test_team_flow_smoke.py` |

---

## Feedback files (transient — deleted after resolution)

Live in `plans/production-readiness-hardening/feedback/`. A file existing = issue open.

| File | Written by | Resolved by |
|---|---|---|
| `REVIEW_FAILURES.md` | Reviewer | Builder |
| `TEST_FAILURES.md` | Tester | Builder |
| `IMPL_QUESTIONS.md` | Builder [REQ] | Planner |
| `DESIGN_QUESTIONS.md` | Builder [ARCH] | Architect |
| `HUMAN_QUESTIONS.md` | Any agent | User |
