# Pathly Engine System Review

Internal review of pathly-engine's current shape and release posture.

## Current Strengths

- Files are the protocol: plans, feedback files, `STATE.json`, and
  `EVENTS.jsonl` make workflow state inspectable and recoverable.
- Role contracts are explicit: planner plans, builder implements, reviewer
  reports, tester verifies, and orchestrator routes.
- The FSM is deterministic: `reducer.py` is a pure function with no I/O,
  making every transition auditable and testable.
- The Python team-flow driver keeps the terminal CLI path alive — `pathly flow`
  works outside Claude Code without requiring any host tool.
- The event log is append-only: state can always be reconstructed from events
  even if `STATE.json` is lost or corrupt.
- Feedback TTL and orphan detection let the startup check auto-resolve stale
  blockers without human intervention.
- `strict` workflow correctly rejects `fast` mode — human approval gates cannot
  be skipped at the highest rigor level.

## Current Risks

- pathly-engine is still a public beta candidate, not production-ready.
- End-to-end agent behavior still needs manual smoke validation in Claude Code
  and Codex before broad release claims.
- `subprocess.run()` calls do not set timeouts — long-running or hung agent
  processes could stall a workflow indefinitely.
- Recovery behavior (corrupt `EVENTS.jsonl`, missing `STATE.json`, stale
  feedback) is not fully covered by automated tests.
- The trust model for project rules, PRDs, plans, and generated prompts is not
  documented in one place.
- The `meet` CLI depends on the `claude` command for read-only consultation at
  runtime.

## Design Decisions To Preserve

- Keep `po` optional and on-demand.
- Keep `architect` consultation tied to real design uncertainty or risk.
- Keep builder consultation constrained to specific questions and outputs.
- Keep `meet` read-only by default; it writes consult notes, not source code.
- Keep `director` out of the default `meet` target list.
- Keep core prompts host-neutral; adapters own slash-command or plugin syntax.
- Keep `orchestrator/reducer.py` a pure function — no I/O, no side effects.
- Keep `EVENTS.jsonl` append-only.
- Keep retry keys bound to `created_by_event`, not conversation number.

## Current Implementation Map

```text
pathly-engine/orchestrator/       pure FSM library: reducer, state, events,
                                  feedback, event log
pathly-engine/runners/            Claude/Codex runner abstractions
pathly-engine/team_flow/          Python team-flow driver: manager, prompts,
                                  filesystem, config
pathly-engine/engine_cli/         CLI entry point (pathly command)
tests/                            FSM checks, event log persistence, TTL,
                                  protocol alignment, driver-support edge cases
```

## Recommended Next Hardening

1. Add subprocess timeouts and failure-policy tests for all runner calls.
2. Add end-to-end smoke tests for lite flow, nano flow, build entry, test entry,
   feedback loop handling, and zero-diff stall handling.
3. Add path canonicalization for hook writes and extend feature-name validation
   to every non-CLI entry point.
4. Add trust-boundary documentation for PRDs, plans, `.claude/rules/`, and
   generated prompts, with static tests for critical prompt clauses.
5. Keep release docs and README wording at public beta until the smoke matrix
   and public walkthroughs exist.
