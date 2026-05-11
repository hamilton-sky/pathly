# Pathly Engine Security and Reliability Review

This document records the current security/reliability posture for pathly-engine
and the remaining hardening work before a production-ready label.

Current status: public beta candidate.

The architecture has good safety properties: file-based handoffs, deterministic
FSM recovery, explicit feedback files, human pause points, and scoped agent
roles. The main production gaps are end-to-end workflow tests, stricter
validation around hook file paths, clearer subprocess failure policy, and a
security pass over generated prompts and trusted/untrusted file boundaries.

---

## Subprocess Calls

Files reviewed:

- `pathly-engine/team_flow/manager.py`
- `pathly-engine/runners/`
- skill docs that instruct `git diff`, `git status`, and verification commands

Risk:

- The driver spawns `claude -p` subprocesses.
- The driver calls `git diff`, `git status`, and `claude --version`.
- Long-running or hung subprocesses could stall a workflow.

Mitigation today:

- Python subprocess calls use argument lists rather than shell string
  interpolation.
- The main Python driver runs from the repository root.
- The reviewer prompt in `pathly-engine/team_flow/manager.py` reviews
  working-tree changes with `git diff HEAD -- . ':(exclude)plans/'`.
- Pre-flight checks stop when `claude` is unavailable.

Remaining gap:

- `subprocess.run()` calls do not set timeouts.
- Failure handling varies by stage; some warnings proceed while other failures
  stop. A single policy is needed.

Production recommendation:

- Add subprocess timeouts and clear timeout messages for all supporting
  subprocess calls.
- Keep runner timeout and failure policy covered by focused tests before a
  production release.
- Add smoke tests that mock `subprocess.run()` for clean, failed, and timeout
  cases.
- Define a single policy for when subprocess failure blocks the pipeline versus
  when it can continue with a warning.

---

## Generated Prompts and Prompt Injection

Files reviewed:

- `pathly-adapters/core/skills/team-flow.md`
- `pathly-adapters/core/skills/go.md`
- `pathly-adapters/core/skills/plan.md`
- `pathly-adapters/core/skills/prd-import.md`
- `pathly-adapters/core/agents/director.md`

Risk:

- Plans and PRDs can contain untrusted user or generated text.
- Generated builder/reviewer prompts may include instructions from project files.
- `.claude/rules/` and plan files are intentionally trusted by the framework,
  but malicious or stale content there could steer agent behavior.

Mitigation today:

- Agent roles have explicit boundaries: builder implements, reviewer reviews,
  tester verifies, orchestrator delegates.
- Builder instructions emphasize scope control and no silent refactors.
- Reviewer is adversarial and should catch contract violations.
- Feedback files route ambiguity to planner/architect/human rather than
  allowing silent continuation.

Remaining gap:

- The trust model for project rules, PRDs, plans, and generated prompts is not
  documented in one place.
- There are no tests that verify prompt templates contain required safety
  boundaries.

Production recommendation:

- Add a "Trust Boundaries" section to docs (see below).
- Require generated prompts to label PRD/user text as requirements context, not
  executable instructions.
- Add static tests for critical prompt clauses: scope limits, feedback handling,
  review gates, and no direct implementation by Director/Orchestrator.

---

## Trust Boundaries

Pathly treats these files as trusted workflow inputs once they are in the
project workspace:

- `plans/<feature>/*.md` plan files.
- PRDs imported through `prd-import` or `bmad-import`.
- Project rules such as `.claude/rules/` when present.
- Feedback files under `plans/<feature>/feedback/`.

User-provided PRD text and generated plan text should be quoted or summarized
as requirements context, not obeyed as higher-priority runtime instructions.
Agent contracts remain the authority for role boundaries: Director and
Orchestrator route, Planner and Architect design, Builder edits source,
Reviewer reports, and Tester verifies.

Precedence (highest to lowest):

1. Pathly role contracts (behavioral contracts in `core/agents/`)
2. User request
3. Project rules (`.claude/rules/`)
4. Plan files (`plans/<feature>/`)
5. Generated feedback

Production hardening still needed:

- Static tests for prompt clauses that label imported PRD/user text as context.
- A single documented precedence order for user request, project rules, Pathly
  role contracts, plan files, and generated feedback.

---

## File Writes and STATE.json Integrity

Files reviewed:

- `pathly-engine/orchestrator/eventlog.py`
- `pathly-engine/orchestrator/reducer.py`
- `pathly-engine/orchestrator/state.py`
- `pathly-engine/team_flow/manager.py`
- feedback-file protocol docs

Risk:

- State is stored on disk in `plans/<feature>/EVENTS.jsonl` and `STATE.json`.
- Feedback files are control-plane signals.
- Partial writes or corrupt state files could desynchronize the pipeline.
- Auto-deleting expired feedback files could remove a still-relevant blocker if
  TTL metadata is wrong.

Mitigation today:

- `EVENTS.jsonl` is append-only.
- State can be reconstructed from events.
- Startup integrity checks look for orphan/expired feedback and FSM drift.
- Disk feedback wins over stale `STATE.json`.
- `EventLog` handles filename-only paths safely.

Remaining gap:

- `STATE.json` writes are atomic, but event-log appends and other generated
  files still need a broader failure-policy review.
- Event log corruption handling is limited.
- Feature names are validated by the CLI, but every non-CLI entry point should
  keep equivalent path traversal protections.
- Safe-delete decisions rely on metadata quality.

Production recommendation:

- Keep atomic writes for `STATE.json` and extend the policy to any generated
  JSON files that are rewritten.
- Keep feature-name validation covered by tests and mirror it in adapter paths
  that create plan directories.
- Add tests for corrupt `EVENTS.jsonl`, missing `STATE.json`, stale feedback,
  and path traversal attempts.
- Keep safe-delete operations visible in logs and reversible where possible.

---

## Human Gates and Recovery

Files reviewed:

- `pathly-engine/team_flow/manager.py`
- `pathly-adapters/core/skills/team-flow.md`
- `docs/ORCHESTRATOR_FSM.md`
- `docs/FEEDBACK_PROTOCOL.md`

Risk:

- Fast/auto modes can skip human pause points.
- Strict workflows must not skip approval gates.
- Retry loops can waste time or repeatedly modify files without progress.

Mitigation today:

- `strict` rejects `fast`.
- Feedback files block forward progress.
- Max retry cycles are enforced.
- Zero-diff stalls escalate to `HUMAN_QUESTIONS.md`.
- Startup checks stop fast mode on real drift issues.

Remaining gap:

- Recovery behavior needs more end-to-end tests.
- Some manual-control paths are documented but not validated by automated smoke
  tests.

Production recommendation:

- Add smoke tests for lite flow, nano flow, build entry, test entry, feedback
  handling, and zero-diff stall handling.
- Add a release checklist requiring one manual smoke run through `/pathly ...`
  in Claude Code, one `Use Pathly ...` run in Codex, and one direct
  `pathly flow ...` CLI run.

---

## Production Readiness Checklist

Required before production-ready:

- GitHub Actions green on supported Python versions.
- End-to-end smoke tests for: lite flow, nano flow, build entry, test entry,
  feedback loop handling, zero-diff stall handling.
- Subprocess timeout policy implemented.
- Trust-boundary documentation for PRDs, plans, `.claude/rules/`, and
  generated prompts.
- Release/versioning policy with changelog and compatibility notes.

Recommended before public beta:

- Keep hooks optional and documented.
- Add a quick manual smoke-test guide.
- Verify README installation flow on clean Claude Code and Codex setups.
