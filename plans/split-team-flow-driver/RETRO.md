# split-team-flow-driver - Retrospective

## Plan Quality
**Conversation sizing:** Good. The work split cleanly into three small slices: runner extraction, feedback helper extraction, and final driver cleanup.

**Surprises:** Verification exposed a sandbox-specific temp directory issue when `PYTEST_TMPDIR` was overridden. The default `pytest -q` path remained green, and `.pytest-tmp/` is now ignored as generated test output.

**Missing from plan:** The original plan implied conversation dependencies by phase order. A planner consult promoted explicit dependency lines into the plan before implementation started.

## What Worked
- Extracting `AgentRunner` first made subprocess command shape, usage parsing, and timeout behavior directly testable.
- Extracting feedback priority into `orchestrator/feedback.py` kept file protocol policy separate from the driver loop.
- Keeping `Driver.run_claude(...)` as a thin wrapper preserved the existing behavior surface while moving implementation detail out of `scripts/team_flow.py`.
- Full `pytest -q` stayed green after each extraction checkpoint.

## What to Improve Next Time
- Add explicit `Depends on` lines during planning, not during a later consult promotion.
- Avoid changing `PYTEST_TMPDIR` during verification unless the target directory has already been proven writable and removable in the current sandbox.
- When extracting driver collaborators, add the focused tests before widening smoke-test runs; it makes failures easier to classify.

## Seed for Next Storm
> For driver refactors, split by collaborator boundary and keep the public wrapper in place until the extracted module has direct tests. Make dependencies explicit in the conversation guide before build starts, especially when later conversations rely on earlier extracted modules.
