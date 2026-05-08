# installable-workflow-architecture - Implementation Plan

## Overview

This feature makes Pathly's installable architecture real in small, testable
increments. It first establishes package resource loading and clean install
smoke coverage, then adds transparent setup diagnostics, safe adapter
materialization, recovery/status UX, hook hardening, and documentation alignment.

The implementation must preserve Pathly's product boundaries: Pathly is the
workflow brain, host adapters are thin surfaces, filesystem state remains the
source of truth, hooks are guardrails, and lifecycle routing stays under the
orchestrator/FSM rather than setup or hooks.

## Layer Architecture

```text
Host surfaces
  Claude Code, Codex, CLI
        |
        v
CLI command layer
  pathly/cli/manager.py
  pathly/cli/setup_command.py
  pathly/cli/status_command.py
        |
        v
Setup/resource layer
  pathly/resources.py
  pathly/setup/locations.py
  pathly/setup/detect.py
  pathly/setup/plan.py
  pathly/setup/materialize.py
        |
        v
Packaged assets and runtime
  core/
  adapters/
  pathly/hooks/
  orchestrator/
        |
        v
Project filesystem
  plans/<feature>/
  feedback/
  consults/
  STATE.json and EVENTS.jsonl
```

## Phases

### Phase 1: Package resource contract
**Layer:** Packaging/runtime resources
**Delivers stories:** S1.1
**Purpose:** Give Pathly one host-neutral API for reading and copying packaged
assets.
**Depends on:** Existing `pyproject.toml` package metadata, `core/`, and
`adapters/`.
**Enables:** CLI, setup, doctor, and installers can use assets without
repo-root assumptions.
**Files:**
- `pathly/resources.py` - NEW: package resource lookup and copy helpers.
- `pyproject.toml` - package data/resource declarations if needed.
- `tests/test_project_packaging.py` - asset/resource coverage.

**Details:**
- Add helpers for prompt, template, agent, adapter manifest, and skill asset
  paths.
- Prefer `importlib.resources` semantics over direct `Path(__file__).parents`
  access for packaged assets.
- Provide a copy/materialization helper that preserves relative paths.
- Return clear errors when required packaged assets are missing.

**Verification:** `pytest tests/test_project_packaging.py -q`; `python -m build`

### Phase 2: Clean install smoke and version command
**Layer:** Packaging/CLI
**Delivers stories:** S1.2
**Purpose:** Prove installed Pathly works from a fresh environment and a
non-Pathly project directory.
**Depends on:** Phase 1 resource contract.
**Enables:** Setup and doctor can be built on a verified installed-package
contract.
**Files:**
- `pathly/cli/manager.py` - add `--version` wiring or parser behavior.
- `pathly/__init__.py` - expose package version if appropriate.
- `tests/test_project_packaging.py` - wheel or isolated install smoke.
- `tests/test_cli.py` - `--version` and non-Pathly command behavior.

**Details:**
- Add a `pathly --version` path using package metadata.
- Add a smoke test that builds or installs the package into a fresh environment
  where practical.
- Confirm `pathly --help`, `pathly doctor`, and `pathly help` do not depend on
  the repo checkout.
- Keep missing Claude/Codex CLIs as diagnostics, not Pathly install failures.

**Verification:** `python -m build`; installed-wheel smoke; `pytest tests/test_cli.py tests/test_project_packaging.py -q`

### Phase 3: Setup diagnostics and dry run
**Layer:** CLI/setup
**Delivers stories:** S2.1
**Purpose:** Make setup transparent before any file mutation.
**Depends on:** Phases 1-2.
**Enables:** Users can inspect host detection, planned writes, planned hook
registration, conflicts, and start commands.
**Files:**
- `pathly/cli/setup_command.py` - NEW: setup command orchestration.
- `pathly/setup/detect.py` - NEW: host detection.
- `pathly/setup/locations.py` - NEW: user data and host location rules.
- `pathly/setup/plan.py` - NEW: setup action plan/dry-run model.
- `pathly/cli/manager.py` - parser/dispatch wiring only.
- `tests/test_setup.py` - NEW: dry-run and detection tests.

**Details:**
- Add `pathly setup`, `pathly setup --dry-run`, `pathly setup claude --dry-run`,
  and `pathly setup codex --dry-run`.
- Default `pathly setup` to a safe report unless `--apply` is present.
- Report detected hosts, Pathly version, planned adapter writes, planned hook
  registration, conflicts, and final start commands.
- Ensure dry run performs no writes.

**Verification:** `pytest tests/test_setup.py -q`; `pathly setup --dry-run`

### Phase 4: Adapter materialization
**Layer:** Setup/adapters
**Delivers stories:** S2.2
**Purpose:** Install or repair host adapter files from packaged resources into
approved user-level locations.
**Depends on:** Phase 3 dry-run plan and Phase 1 resources.
**Enables:** `pathly setup --apply`, host-specific setup apply, repair, and
force behavior.
**Files:**
- `pathly/setup/materialize.py` - NEW: safe copy/repair/force behavior.
- `pathly/cli/installers/codex.py` - refactor toward resource-backed behavior.
- `pathly/cli/setup_command.py` - apply/repair/force handling.
- `tests/test_setup.py` - temp-home materialization tests.
- `adapters/codex/README.md` and `adapters/claude-code/README.md` - align if
  command behavior changes.

**Details:**
- Use versioned user data snapshots, for example
  `%LOCALAPPDATA%\Pathly\adapters\<version>\...` on Windows and an
  XDG-compatible data location on macOS/Linux.
- Copy assets from packaged resources instead of creating junctions to the
  source checkout.
- Track Pathly-owned files enough to support repair and safe replacement.
- Preserve Codex natural-language invocation guidance.

**Verification:** `pytest tests/test_setup.py -q`; `pytest tests/test_cli.py -q`

### Phase 5: Status and doctor UX
**Layer:** CLI/workflow status
**Delivers stories:** S3.1
**Purpose:** Make install, adapter, hook, and workflow recovery state readable
without exposing raw FSM internals by default.
**Depends on:** Existing `orchestrator/` state/event packages and setup
diagnostics.
**Enables:** Users can resume safely after interruption.
**Files:**
- `pathly/cli/status_command.py` - NEW: project/feature status rendering.
- `pathly/cli/manager.py` - parser/dispatch wiring.
- `pathly/cli/help_command.py` - share status logic where appropriate.
- `pathly/cli/plans.py` - reusable workflow-state queries if needed.
- `tests/test_cli.py` or `tests/test_status.py` - status and doctor cases.

**Details:**
- Add `pathly status [feature]`.
- Show current state, active feedback, next owner, and suggested command.
- Make `doctor` distinguish install, adapter, hook, and workflow state issues.
- Keep raw event names hidden unless diagnostics are requested.

**Verification:** `pytest tests/test_cli.py -q`; `pathly status`; `pathly doctor`

### Phase 6: Hook hardening
**Layer:** Runtime hooks
**Delivers stories:** S3.2
**Purpose:** Keep hooks deterministic, visible, and bounded.
**Depends on:** Existing `pathly/hooks/` runtime and setup/apply behavior.
**Enables:** Optional hook automation without hidden workflow execution.
**Files:**
- `pathly/hooks/contracts.py` - payload/path validation.
- `pathly/hooks/inject_feedback_ttl.py` - metadata injection boundaries.
- `pathly/hooks/classify_feedback.py` - classification boundaries.
- `pathly/cli/hooks_command.py` - diagnostics and install/report behavior.
- `tests/test_hooks.py` - malformed payload, traversal, ignored path, and
  diagnostics coverage.

**Details:**
- Canonicalize hook target paths before writes.
- Ensure hook writes stay under the active project `plans/` directory.
- Emit visible diagnostics for malformed payloads and unsupported hosts.
- Do not spawn agents, edit source code, or advance lifecycle state from hooks.

**Verification:** `pytest tests/test_hooks.py -q`; `pytest -q`

### Phase 7: Host smoke and docs alignment
**Layer:** Docs/host surfaces
**Delivers stories:** S4.1
**Purpose:** Make README, adapter docs, and setup output match verified behavior.
**Depends on:** Phases 1-6.
**Enables:** Honest beta onboarding for CLI, Claude Code, Codex, and hooks.
**Files:**
- `README.md` - install, setup, status, and limitation updates.
- `docs/PRODUCTION_READINESS.md` - release gate updates.
- `docs/INSTALLABLE_WORKFLOW_ARCHITECTURE_PROPOSAL.md` - mark implemented
  decisions or update order if needed.
- `docs/INSTALLABLE_WORKFLOW_ARCHITECTURE_RECOMMENDATIONS.md` - mark accepted
  phase order.
- `adapters/*/README.md` - host-specific setup and smoke commands.
- `tests/test_project_packaging.py` - static docs/command alignment.

**Details:**
- Document only verified host behavior.
- Keep Codex as natural-language skill invocation.
- Keep Claude Code slash-command examples separate from Codex examples.
- Preserve public beta candidate language.

**Verification:** `pytest -q`; manual host smoke matrix where hosts are available.

## Prerequisites

- Baseline `pytest -q` should be green or known failures should be recorded
  before Conversation 1 starts.
- Python build tooling must be available through the dev extra or installed in
  the active environment.
- Host smoke for Claude Code and Codex is optional until those hosts are
  available on the verification machine.

## Key Decisions

- Setup must not become lifecycle authority. It detects hosts and writes adapter
  assets only when explicitly applying a setup plan.
- Adapter assets should be copied into versioned user data snapshots rather than
  registered directly from a Python package install location. This makes repair,
  inspection, and host registration clearer.
- Hooks remain guardrails. They validate, classify, annotate, and report; they do
  not spawn lifecycle agents or advance FSM state.
- `po` remains optional and on-demand. This plan has enough product intent, so no
  PO stage is included.
- `architect` input is captured in this plan, but architect is not added as a
  default runtime stage.
