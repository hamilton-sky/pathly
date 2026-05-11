# Pathly Engine Production Readiness

Release criteria for pathly-engine. Until these gates are met, describe
pathly-engine publicly as a public beta / technical preview.

## Release Position

pathly-engine is currently:

- Public beta candidate.
- Packaged as a Python CLI named `pathly` for install guidance, project plan
  initialization, status menus, doctor checks, and the Python team-flow driver.
- Not yet production-ready: end-to-end agent runs, hook hardening, and
  release/versioning policy still need to be finished.

Current CLI scope:

- `pathly init <feature>` creates a lite starter plan.
- `pathly help`, `pathly doctor`, `pathly debug`, `pathly explore`, and
  `pathly review` expose stable local fallback surfaces.
- `pathly flow <feature>` runs the Python team-flow driver when the required
  runner tooling is available.
- `pathly meet [feature]` writes read-only consultation notes under
  `plans/<feature>/consults/` when the required runner tooling is available.
- `pathly status [feature]` reports current FSM state and the suggested next
  action.

Recommended next:

- Add `pathly uninstall` only when it can clean up each supported adapter safely.
- Add a manual smoke-test guide that records one successful run through each
  major front door: `go`, `debug`, `explore`, `review`, and `doctor`.

## FSM Tests

Required before production-ready:

- `pytest -q` passes on Python 3.11, 3.12, and 3.13.
- GitHub Actions green on all supported Python versions.
- FSM reducer unit tests: every documented state transition covered.
- Event log tests: append, read, corruption handling, and orphan detection.
- Feedback TTL tests: not-expired, expired, long-pause false positives, missing
  frontmatter, and orphan detection.
- Protocol alignment test: Python `FeedbackFile` constants and Markdown docs
  reference the same filenames.

## Team-Flow Driver

Required before production-ready:

- End-to-end smoke tests for:
  - lite flow (full pipeline)
  - nano flow (direct build, no plan)
  - build entry (skip to implementation)
  - test entry (skip to test stage)
  - feedback loop handling (REVIEW_FAILURES.md → builder → resolve)
  - zero-diff stall handling (HUMAN_QUESTIONS.md [STALL])

## CLI Commands

Required before production-ready:

- Every README command maps to a live parser command.
- `pathly --version` works from a clean virtual environment.
- `pathly doctor` clearly distinguishes missing host tools from engine install
  failures.
- Diagnostics work from a non-Pathly project directory.
- No command depends on a specific checkout path.

## Hook Policy

Required before production-ready:

- Hook unit tests for: ignored paths, malformed JSON, already-tagged files,
  missing API key, existing `DESIGN_QUESTIONS.md`, and TTL frontmatter.
- Path canonicalization before every hook write.
- Hook failures are logged in a project-local diagnostic file.
- Pipeline functions correctly without hooks installed (hooks are optional).

## State Recovery

Required before production-ready:

- `STATE.json` writes are atomic.
- Event-log appends handle partial write failure.
- Feature-name validation covers path traversal attempts.
- Recovery from corrupt `EVENTS.jsonl`, missing `STATE.json`, and stale
  feedback is covered by tests.
- `verify-state` detects and reports `STATE.json` / feedback file mismatch.

## Feedback TTL

Required before production-ready:

- Default TTL is 168 hours (1 week) — avoids false positives when users pause
  for days.
- Clock is injectable for testing.
- Orphan detection uses `created_by_event` to match against `EVENTS.jsonl`.
- Auto-delete decisions are logged and visible.

## Rigor Modes

Required before production-ready:

- `strict` rejects `--fast` unconditionally.
- Rigor escalator transitions are one-way.
- Escalation at `BUILDING` pauses at `IMPLEMENT_PAUSED` and notifies the user.
- Retry keys bound to `created_by_event`, not conversation number.

## Subprocess Policy

Required before production-ready:

- All `subprocess.run()` calls set timeouts.
- Timeout and failure cases covered by focused tests.
- Failure policy is documented: which failures block the pipeline vs. continue
  with a warning.

## Naming

Public brand: `Pathly`
Python distribution: `pathly-engine`

Before publishing broadly:

- Check GitHub repository name availability.
- Check PyPI package name `pathly-engine` availability.

## Quality Gates

Required before production-ready:

- `pytest -q` passes.
- GitHub Actions green on Python 3.11, 3.12, and 3.13.
- Security and reliability notes are current.
- Public known-limitations section exists in README.
- At least three public walkthroughs or case studies exist:
  - Tiny change through `nano`.
  - Bug fix through `debug`.
  - Feature through `lite` or `standard`.

Recommended:

- Changelog for every public release.
- Version tag before large restructuring.
- Example walkthroughs of `pathly flow` from the CLI.
