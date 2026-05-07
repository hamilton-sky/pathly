# clean-filesystem - User Stories

## Context

Pathly currently has a working instruction layer and a Python runtime layer, but
the filesystem still carries legacy bridge files, candidate modules, shell hook
installers, and generated mirrors that can drift from the canonical adapters.
This feature gives maintainers one predictable repo shape before broader
production hardening.

The user benefit is operational clarity: installs should include runtime code,
core prompts, adapters, and templates reliably; the FSM should call a
host-neutral runner; hooks should be portable; and legacy files should be
deleted only after replacements and packaging checks pass.

## Target Shape

Pathly should converge on this repository layout:

```text
core/                 canonical prompts, agents, and templates
adapters/             Claude Code and Codex plugin wrappers
pathly/               Python runtime packages
pathly/runners/       Claude/Codex execution layer
pathly/hooks/         portable hook behavior
orchestrator/         deterministic FSM core for this plan
tests/                repo-level tests
.agents/plugins/      marketplace metadata
.agents/skills/       direct skill-discovery mirror, if still needed
```

The plan intentionally does not move `orchestrator/` under `pathly/`, does not
move tests into `pathly/tests/`, and does not create `pathly/scripts/`.

## Stories

### Story 1.1: Runtime entrypoints are canonical
**As a** Pathly maintainer, **I want** CLI and team-flow entrypoints to resolve
through canonical packages, **so that** installed and local execution use the
same runtime path.

**Acceptance Criteria:**
- [ ] `python -m pathly.cli --help` exits successfully.
- [ ] `python -m pathly.team_flow --help` exits successfully.
- [ ] `pathly --help` exits successfully from the project environment.
- [ ] Tests no longer import team-flow behavior from `scripts.team_flow`.
- [ ] `pytest -q` passes.

**Edge Cases:**
- Existing `pathly` console script behavior remains compatible.
- Any bridge file kept during migration is temporary and documented in the
  implementation notes.

**Delivered by:** Phase 1 -> Conversation 1

### Story 1.2: Runtime code is packaged predictably
**As a** Pathly maintainer, **I want** packaging metadata to include runtime
packages and non-runtime assets intentionally, **so that** wheel and sdist
installs contain the files Pathly needs outside the source checkout.

**Acceptance Criteria:**
- [ ] Package metadata treats `pathly/` as the primary runtime package.
- [ ] `orchestrator/` remains available as the deterministic FSM core package.
- [ ] `core/` prompts, agents, and templates are included as package data or
  otherwise verified in built artifacts.
- [ ] `adapters/` plugin metadata and skill files are included as package data
  or otherwise verified in built artifacts.
- [ ] Tests remain repo-level under `tests/`.
- [ ] `python -m build` completes successfully.

**Edge Cases:**
- `examples/` remains root-level public sample material.
- Generated folders such as `.pytest-tmp/`, `.pytest_cache/`, `logs/`, and
  `*.egg-info/` remain ignored rather than packaged.

**Delivered by:** Phase 5 -> Conversation 4

### Story 2.1: Agent execution uses a host-neutral runner
**As a** Pathly maintainer, **I want** the Python FSM to depend on a runner
interface, **so that** Claude CLI and Codex CLI execution can be selected
without embedding host-specific behavior in the workflow driver.

**Acceptance Criteria:**
- [ ] A shared runner contract exposes return code, stdout, stderr, and usage
  metadata.
- [ ] Claude runner behavior remains compatible with current Claude CLI
  execution and usage parsing.
- [ ] Codex runner has command-construction tests.
- [ ] Runtime selection accepts `claude`, `codex`, and `auto`.
- [ ] `pytest -q` passes.

**Edge Cases:**
- Codex usage metadata may be empty when no stable machine-readable output is
  available.
- `PATHLY_RUNNER` can provide a fallback selection when no explicit runner is
  passed.

**Delivered by:** Phase 2 -> Conversation 2

### Story 3.1: Hooks are portable runtime modules
**As a** Pathly maintainer, **I want** hook logic under `pathly/hooks/`, **so
that** Claude Code, Codex, and cloud workflows can call the same behavior
without relying on root-level scripts.

**Acceptance Criteria:**
- [ ] Hook logic lives under `pathly/hooks/`.
- [ ] A CLI surface can print Claude hook config.
- [ ] A CLI surface can run a hook event from a JSON payload.
- [ ] Root hook scripts are no longer required by runtime code.
- [ ] `pytest -q` passes.

**Edge Cases:**
- Codex is treated as skill/plugin based unless a documented native hook schema
  exists.
- Host-native hook support is optional; runtime checkpoint calls remain valid.

**Delivered by:** Phase 3 -> Conversation 3

### Story 4.1: Legacy files are removed only after replacements pass
**As a** Pathly maintainer, **I want** legacy bridge files, candidate modules,
shell installers, and generated mirrors removed or generated only after tests
prove replacements work, **so that** cleanup does not break local or installed
Pathly workflows.

**Acceptance Criteria:**
- [ ] No runtime imports depend on `scripts/`.
- [ ] Candidate names such as `cli-2` are absent from runtime paths.
- [ ] Root `hooks/` is absent after `pathly/hooks/` is packaged and tested.
- [ ] Runtime behavior formerly in `scripts/` lives in responsibility-based
  modules, not in a new `pathly/scripts/` package.
- [ ] `.agents/skills/` is either generated or exact-mirror verified against
  `adapters/codex/skills/`.
- [ ] `pytest -q` passes after cleanup.

**Edge Cases:**
- Deletion is deferred when a replacement test or packaging check fails.
- Any compatibility exception is documented in the plan progress notes before
  the conversation is marked done.

**Delivered by:** Phase 4 -> Conversation 4
