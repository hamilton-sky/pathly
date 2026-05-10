# Installable Workflow Architecture Recommendations

> **Superseded** — consolidated into [INSTALLER_DESIGN.md](INSTALLER_DESIGN.md). This file is kept for git history.

## Summary

The installable workflow proposal is directionally correct. Pathly should remain
the workflow brain, host adapters should stay thin, and the filesystem/FSM model
should remain the source of truth.

The main improvement is implementation order. Before adding a broad `pathly
setup` experience, Pathly should first prove that an installed wheel can find
its own assets, run diagnostics from any project, and expose stable adapter
resources without relying on a source checkout.

## Recommendation

Proceed with the proposal, but add an explicit Phase 0 and make setup
mutation-driven only after dry-run diagnostics are reliable.

Recommended phase order:

| Phase | Purpose | Why it comes here |
|---|---|---|
| 0 | Package resource contract | Removes repo-relative assumptions before setup depends on assets. |
| 1 | Clean install smoke | Proves `pip install pathly` works outside the source checkout. |
| 2 | Setup diagnostics and dry run | Lets users see detected hosts and planned writes before mutation. |
| 3 | Adapter materialization | Installs or repairs host adapters using the resource contract. |
| 4 | Status and doctor UX | Makes interrupted workflow state understandable. |
| 5 | Hook hardening | Adds optional automation after the base workflow is dependable. |
| 6 | Host smoke and docs alignment | Verifies Claude Code, Codex, and CLI behavior match docs. |

## Phase 0: Package Resource Contract

**Purpose:** Give Pathly one host-neutral way to load packaged assets.

**Why:** Current architecture depends on core prompts, role contracts, templates,
and adapter files. Those assets must be available from an installed package, not
only from a cloned repository.

**Tasks:**

- Add a small internal resource API, for example `pathly.resources`.
- Load prompts, templates, adapter manifests, and skill files through that API.
- Replace direct repo-root assumptions in CLI and installer code.
- Prefer package-relative resources over ad hoc filesystem paths.
- Add tests that exercise resource loading from an installed wheel or isolated
  package path.

**Verification:**

```bash
python -m build
python -m venv .tmp/pathly-install-smoke
.tmp/pathly-install-smoke/Scripts/python -m pip install dist/pathly-*.whl
.tmp/pathly-install-smoke/Scripts/pathly --version
.tmp/pathly-install-smoke/Scripts/pathly doctor
```

## Phase 1: Clean Install Smoke

**Purpose:** Prove Pathly works without the source checkout.

**Tasks:**

- Build the wheel.
- Install it into a fresh virtual environment.
- Run `pathly --version`, `pathly --help`, `pathly doctor`, and `pathly help`
  from a temporary non-Pathly project directory.
- Confirm no command depends on `C:\Users\Yafit\pathly` or another checkout
  path.

**Acceptance Criteria:**

- The CLI entry point works from a clean virtual environment.
- Package assets are readable from installed package resources.
- Diagnostics clearly distinguish missing host tools from Pathly install
  failures.

## Phase 2: Setup Diagnostics And Dry Run

**Purpose:** Make setup transparent before it writes files.

**Recommended command behavior:**

```text
pathly setup
pathly setup --dry-run
pathly setup claude --dry-run
pathly setup codex --dry-run
pathly setup --apply
```

`pathly setup` should default to a safe report unless the proposal explicitly
chooses mutation by default. A dry run should show:

- detected hosts
- Pathly version
- planned adapter writes
- planned hook registration
- existing files that would be replaced or repaired
- final user command for each host

**Acceptance Criteria:**

- No files are written during dry run.
- Output ends with host-specific start commands.
- Unsupported or missing hosts produce useful next steps.

## Phase 3: Adapter Materialization

**Purpose:** Install or repair host adapter files from packaged resources.

**Tasks:**

- Define user-level Pathly data locations explicitly.
- Stop using temporary paths as default long-term adapter locations.
- Add `--force` for replacement and `--repair` for stale Pathly-owned files.
- Keep Codex wording as natural language, not slash commands.
- Keep Claude Code slash-command docs separate from Codex plugin docs.

**Recommended storage rule:**

| Platform | User-level Pathly data |
|---|---|
| Windows | `%LOCALAPPDATA%\Pathly\` or `%APPDATA%\Pathly\` |
| macOS/Linux | XDG-compatible data directory |
| Project state | Always under the active project `plans/` directory |

## Phase 4: Status And Doctor UX

**Purpose:** Let users recover after interruption without reading raw FSM
internals.

**Tasks:**

- Add or refine `pathly status [feature]`.
- Summarize current state, active feedback, next owner, and suggested command.
- Keep raw event names hidden unless diagnostics are requested.
- Make `doctor` distinguish install problems, adapter problems, and workflow
  state problems.

**Acceptance Criteria:**

- Missing state is reported clearly.
- Feedback-blocked state names the blocking feedback file.
- Done state is obvious.
- The next suggested action is a real command for the active host or CLI.

## Phase 5: Hook Hardening

**Purpose:** Keep hooks useful without making them the workflow driver.

**Allowed hook responsibilities:**

- Validate paths.
- Add metadata to known feedback files.
- Emit diagnostics.
- Run fast FSM consistency checks.
- Return control to the host chat.

**Avoid in hooks:**

- long-running workflows
- lifecycle agent spawning
- source edits
- hidden state advancement
- unsupported host schemas presented as working

Hook failures should be visible and recoverable. They should not corrupt
workflow state or make manual CLI usage impossible.

## Phase 6: Host Smoke And Docs Alignment

**Purpose:** Make release claims match actual host behavior.

**Smoke matrix:**

| Surface | Smoke |
|---|---|
| CLI | `pathly go "add password reset"` routes through Director. |
| Claude Code | `/pathly help` and `/pathly add password reset` reach the adapter. |
| Codex | `Use Pathly help` and `Use Pathly to add password reset` select the plugin skill. |
| Hooks | Optional hook install reports exact registered commands and diagnostics. |

Docs should only claim behavior that this matrix verifies.

## Design Boundaries To Preserve

- Director is the front door and does not implement source changes.
- Orchestrator owns lifecycle transitions.
- Filesystem state remains the source of truth.
- Adapters expose host-native commands and metadata only.
- Core prompts, role contracts, templates, and runtime behavior stay in Pathly.
- `po` remains optional and on-demand.
- `architect` remains on-demand unless real design uncertainty exists.
- `meet` remains read-only and excludes `director` as a default target.
- Hooks are guardrails, not the main workflow.

## Main Risks

| Risk | Mitigation |
|---|---|
| Setup becomes too broad too early | Build resource loading and clean install smoke first. |
| Installed package still depends on repo paths | Add package-resource tests and temporary-project smoke tests. |
| Host adapter behavior drifts from docs | Add host-specific smoke checklist and keep public docs conservative. |
| Hooks accidentally become workflow automation | Keep hook responsibilities deterministic and bounded. |
| Existing user installs get overwritten | Add dry run, repair, force, and Pathly-owned file detection. |

## Bottom Line

The proposal is the correct approach, but it should be tightened around one
principle: prove installability before automating setup.

Once Pathly can load its packaged assets, diagnose itself, and run from a clean
environment, `pathly setup` becomes a much safer and clearer next increment.
