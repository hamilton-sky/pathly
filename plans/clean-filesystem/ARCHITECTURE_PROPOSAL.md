# clean-filesystem - Architecture Proposal

## Problem Statement

Pathly has working instructions and runtime code, but its repo shape still mixes
canonical packages with legacy scripts, root hooks, candidate module names, and
duplicated generated skills. That makes packaging and host integration harder
to reason about and increases drift risk.

## Proposed Solution

Move toward one canonical runtime surface: `pathly/` for primary runtime code,
`orchestrator/` for the deterministic FSM core, `core/` and `adapters/` as
installed assets, `pathly/runners/` for host execution, and `pathly/hooks/` for
portable hook behavior. Delete legacy files only after tests and searches prove
the replacements are active.

## Target Filesystem Shape

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
      .claude-plugin\ or plugin metadata
      skills\

  pathly\
    cli\
    team_flow\
    runners\
    hooks\

  orchestrator\
    deterministic FSM core for this plan

  tests\
    repo-level tests

  .agents\
    plugins\
      marketplace.json
    skills\
      direct skill-discovery mirror, if still needed
```

Plugin source folders live under `adapters/`. Generated or machine-local
marketplace folders such as `C:\tmp\pathly-marketplace\plugins\pathly\` are
installation artifacts, not canonical source folders.

Tests remain at repo root in `tests/`. Runtime behavior from legacy `scripts/`
must move into the appropriate package module (`pathly/cli/`, `pathly/hooks/`,
`pathly/team_flow/`, or `pathly/runners/`) instead of creating a new
`pathly/scripts/` catch-all.

## Runtime Breakdown

```text
CLI command
     |
     v
pathly/cli/
     |
     v
pathly/team_flow/ --------> orchestrator/
     |                         |
     v                         v
pathly/runners/          FSM state/events
     |
     +--> claude CLI
     +--> codex CLI

pathly/hooks/
     |
     +--> generated Claude config
     +--> runtime checkpoint calls
     +--> hook CLI execution
```

## Key Design Decisions

### Decision 1: Keep `orchestrator/` as the FSM core
- **Options considered:** Move under `pathly/`, keep as a package, delete during
  cleanup.
- **Chosen:** Keep as a package for this plan.
- **Rationale:** Moving it under `pathly/orchestrator/` is a separate migration
  and should not be combined with filesystem cleanup.

### Decision 2: Treat `core/` and `adapters/` as assets
- **Options considered:** Convert to runtime packages, package as data, leave
  source-only.
- **Chosen:** Include as installed assets, not runtime packages.
- **Rationale:** Prompts, templates, skills, agents, and plugin manifests are
  required by installation workflows but are not Python runtime modules.

### Decision 3: Add runner interface before cleanup
- **Options considered:** Keep Claude-specific calls in the driver, add Codex
  paths ad hoc, introduce shared contract.
- **Chosen:** Introduce `pathly/runners/` with Claude and Codex implementations.
- **Rationale:** The FSM should depend on a stable runner contract, not on a
  host-specific CLI.

### Decision 4: Make hooks portable before deleting root hooks
- **Options considered:** Keep root scripts, move directly into Claude config,
  move into runtime modules.
- **Chosen:** Move hook behavior under `pathly/hooks/` and generate or print host
  config from the CLI.
- **Rationale:** Claude can use native hooks, while Codex and cloud flows need a
  callable runtime path until native hook support is documented.

### Decision 5: Resolve `.agents/skills/` drift explicitly
- **Options considered:** Delete unconditionally, keep unverified, generate, or
  exact-mirror test.
- **Chosen:** Generate during install if possible; otherwise keep only with
  exact-mirror verification.
- **Rationale:** A committed mirror without a test creates drift risk.

### Decision 6: Keep tests repo-level and avoid `pathly/scripts/`
- **Options considered:** Move tests under `pathly/tests/`, move scripts under
  `pathly/scripts/`, or keep clear repo/package boundaries.
- **Chosen:** Keep tests at repo root. Migrate script behavior into named runtime
  modules or delete obsolete scripts after verification.
- **Rationale:** Repo-level tests avoid packaging confusion. A generic
  `pathly/scripts/` package would preserve the current ambiguity under a new
  directory name.

## Public Commands

- `python -m pathly.cli --help`
- `python -m pathly.team_flow --help`
- `pathly --help`
- `pathly team-flow <feature> --runner claude`
- `pathly team-flow <feature> --runner codex`
- `pathly team-flow <feature> --runner auto`
- `pathly hooks run <event> --payload <json>`
- `pathly hooks install claude`
- `pathly hooks print-config claude`
- `pathly hooks print-config codex`
- `pathly hooks print-config cloud`

## Risks

- **Deleting too early:** Mitigate by requiring searches and green tests before
  removing each legacy path.
- **Packaging misses non-Python assets:** Mitigate with artifact-content tests.
- **Codex usage metadata is unstable:** Mitigate by allowing empty usage while
  preserving stdout, stderr, and return code.
- **Hook behavior diverges by host:** Mitigate by keeping one Python hook module
  surface and generating host config from it.
- **Generated skill mirrors drift:** Mitigate by generation or exact-mirror tests.
