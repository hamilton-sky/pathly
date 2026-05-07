# clean-filesystem - Implementation Plan

## Overview

Clean the Pathly repo shape in migration-safe slices: stabilize canonical
package entrypoints, introduce a host-neutral runner, move hooks into runtime
modules, remove legacy files only after replacement tests pass, and finish with
a packaging gate. This plan does not redesign the FSM or change the instruction
layer semantics.

## Layer Architecture

```text
Instruction assets       Runtime packages          Installed CLI
core/ + adapters/   ->   pathly/ + orchestrator/ -> pathly command
                              |
                              v
                       Runner interface
                       claude | codex | auto
                              |
                              v
                         pathly/hooks/
```

## Target Repository Shape

```text
C:\Users\Yafit\pathly\
  core\
    prompts\
    agents\
    templates\
  adapters\
    codex\
      .codex-plugin\
      skills\
    claude-code\
      plugin metadata
      skills\
  pathly\
    cli\
    team_flow\
    runners\
    hooks\
  orchestrator\
  tests\
  .agents\
    plugins\
      marketplace.json
    skills\
```

`adapters/` is the canonical source for host plugin wrappers. Local marketplace
folders under paths such as `C:\tmp\pathly-marketplace\plugins\pathly\` are
generated install artifacts. `tests/` stays at repo root. Legacy `scripts/`
behavior must be either migrated into a named runtime package or deleted after
verification; do not create `pathly/scripts/` as a new catch-all.

## Phases

### Phase 1: Stabilize package entrypoints
**Layer:** CLI runtime / team-flow runtime
**Delivers stories:** S1.1
**Purpose:** Make local module execution and installed console execution resolve
through canonical package entrypoints before legacy files are removed.
**Depends on:** Existing working CLI behavior and current tests.
**Enables:** Runner integration in Phase 2 and safe deletion decisions in Phase 4.
**Files:**
- `pathly/cli/__init__.py` - export the canonical `main`.
- `pathly/cli/__main__.py` - support `python -m pathly.cli`.
- `pathly/team_flow/__init__.py` - expose canonical team-flow runtime entrypoint.
- `pathly/team_flow/__main__.py` - support `python -m pathly.team_flow`.
- `tests/` - update imports away from `scripts.team_flow` where needed.
- `pyproject.toml` - confirm console script target is canonical.

**Details:**
- Keep public CLI commands compatible.
- Do not delete bridge files in this phase.
- Treat retained bridge files as temporary compatibility shims until Phase 4.

**Verification:** `python -m pathly.cli --help`; `python -m pathly.team_flow --help`; `pathly --help`; `pytest -q`

### Phase 2: Introduce runner interface
**Layer:** Runtime orchestration
**Delivers stories:** S2.1
**Purpose:** Decouple the deterministic FSM from Claude-specific subprocess
execution so Claude and Codex can be selected through one contract.
**Depends on:** Phase 1 canonical entrypoints are working.
**Enables:** Future host selection and Codex execution without changing the FSM
state model.
**Files:**
- `pathly/runners/base.py` - define `Runner`, `RunnerResult`, shared errors,
  and timeout defaults.
- `pathly/runners/claude.py` - preserve Claude command shape and usage parsing.
- `pathly/runners/codex.py` - construct Codex CLI execution and document empty
  usage fallback.
- Runtime manager/driver files that currently call host-specific runners.
- `tests/` - focused runner contract, command construction, and selection tests.

**Details:**
- Preserve current Claude behavior as the default until Codex runner tests are
  green.
- Add explicit selection for `--runner claude|codex|auto`.
- Support `PATHLY_RUNNER=claude|codex|auto`.
- If installed Codex CLI lacks stable JSON output, return empty usage metadata
  while preserving stdout, stderr, and return code.

**Verification:** `pytest -q`; `codex exec -C . "Use Pathly help"` when Codex CLI is available

### Phase 3: Modularize hooks
**Layer:** Runtime hooks / host integration
**Delivers stories:** S3.1
**Purpose:** Move hook behavior into importable runtime modules so host-specific
installation is a configuration concern, not a root-script dependency.
**Depends on:** Phase 1 entrypoints are stable; Phase 2 runner changes are not
blocking hook imports.
**Enables:** Deleting root hook scripts and shell installers in Phase 4.
**Files:**
- `pathly/hooks/contracts.py` - shared hook event and payload contract.
- `pathly/hooks/classify_feedback.py` - migrated feedback classification logic.
- `pathly/hooks/inject_feedback_ttl.py` - migrated TTL injection logic.
- CLI command files for `pathly hooks run`, `pathly hooks print-config`, and
  `pathly hooks install claude`.
- `tests/` - fixture-based hook invocation and config rendering tests.

**Details:**
- Keep Claude Code native hook config supported through generated config.
- Treat Codex hooks as not native unless a documented hook schema exists.
- Runtime checkpoints may call hook functions directly where host-native hooks
  are unavailable.
- Do not remove root `hooks/` or shell setup scripts in this phase.

**Verification:** `pathly hooks print-config claude`; `pathly hooks run post-tool-use --payload <fixture-json>`; `pytest -q`

### Phase 4: Remove legacy files and generated drift
**Layer:** Repository hygiene / compatibility
**Delivers stories:** S4.1
**Purpose:** Delete only files that have verified replacements, reducing drift
without breaking active workflows.
**Depends on:** Phases 1 through 3 are complete and green.
**Enables:** A clean filesystem that can be packaged and installed reliably.
**Files:**
- `pathly/cli.py` - delete after package CLI is canonical.
- `pathly/cli-2.py` - delete after no runtime path references it.
- `pathly/team_flow.py` - delete after package team-flow is canonical.
- `scripts/team_flow.py` - delete after no tests or runtime imports need it.
- `scripts/team-flow-auto.sh` - delete after runtime replacement is verified.
- `scripts/setup-hook.sh` and `scripts/setup-hook.ps1` - delete after hook CLI
  install behavior is verified.
- `scripts/__init__.py` - delete if `scripts/` has no remaining runtime role.
- `hooks/` - delete after `pathly/hooks/` is packaged and tested.
- `.agents/skills/` - either generate during install or exact-mirror verify.

**Details:**
- Run searches before deleting each class of file.
- Keep `examples/` at repo root.
- Keep `tests/` at repo root; do not move tests into the runtime package.
- Move runtime behavior from `scripts/` into `pathly/cli/`, `pathly/hooks/`,
  `pathly/team_flow/`, or `pathly/runners/` based on responsibility.
- Keep dev-only helper scripts outside the runtime package if any remain.
- If `.agents/skills/` remains committed for compatibility, add a test that
  verifies it mirrors `adapters/codex/skills/` exactly.
- Do not delete anything whose replacement verification fails.

**Verification:** `rg "scripts.team_flow|pathly.cli-2|pathly/team_flow.py|setup-hook|hooks/" .`; `pytest -q`

### Phase 5: Packaging gate
**Layer:** Packaging / install verification
**Delivers stories:** S1.2
**Purpose:** Prove the cleaned filesystem produces installable artifacts with
runtime packages, prompts, templates, adapters, and plugin metadata present.
**Depends on:** Phase 4 cleanup is complete.
**Enables:** Release-readiness review against the cleaned repository shape.
**Files:**
- `pyproject.toml` - package discovery and package-data declarations.
- `tests/test_project_packaging.py` or equivalent packaging tests.
- Install/packaging docs only if existing docs become inaccurate.

**Details:**
- Verify wheel or sdist contents include `core/prompts/`, `core/agents/`,
  `core/templates/`, adapter skills, adapter agents, and plugin manifests.
- Keep generated folders ignored.
- Do not broaden package scope beyond what runtime and installation require.

**Verification:** `python -m build`; `pipx install --force dist\pathly-*.whl`; `pathly doctor`; `pathly install codex --apply --market C:\tmp\pathly-marketplace`; `pytest -q`

## Prerequisites

- Baseline `pytest -q` should pass before Conversation 1 starts.
- Any unrelated working-tree changes should be committed or intentionally kept
  separate before builders begin deletion work.
- Builders should avoid source changes outside the current conversation scope.

## Key Decisions

- Keep `orchestrator/` as the deterministic FSM core package for this plan.
- Treat `pathly/` as the only primary runtime package.
- Keep `core/` and `adapters/` as installed assets, not runtime packages.
- Keep plugin source folders under `adapters/`; marketplace `plugins/` folders
  are generated install artifacts.
- Keep `tests/` at repo root.
- Do not introduce `pathly/scripts/`; migrate behavior to responsibility-based
  runtime modules or leave dev-only helpers outside the package.
- Preserve Claude behavior while adding Codex as a selectable runner.
- Treat Codex native hooks as unavailable unless a documented hook surface is
  introduced later.
- Delete legacy files only after replacement tests and searches pass.
