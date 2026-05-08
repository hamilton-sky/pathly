# installable-workflow-architecture - Architecture Proposal

## Problem Statement

Pathly has a coherent local workflow model, but install and adapter behavior
still leans on source-checkout paths and manual host setup. That makes the
product harder to use from a normal `pip install pathly` flow and increases
the risk that docs, adapters, CLI behavior, and tests drift.

The architecture increment should make Pathly installable without changing its
core identity: files remain the protocol, adapters remain thin host surfaces,
and the orchestrator remains the lifecycle authority.

## Proposed Solution

Add a package resource layer, setup planning/materialization modules, and status
UX around the existing Pathly runtime. Setup produces a transparent action plan
first, then copies packaged adapter assets into versioned user data snapshots
only when explicitly applied.

```text
User command
    |
    v
pathly CLI
    |
    +--> resources API ---------> packaged core/adapters assets
    |
    +--> setup plan ------------> dry-run report
    |          |
    |          v
    |      materialize ---------> versioned user data snapshots
    |
    +--> status/doctor ---------> project plans and diagnostics
    |
    v
orchestrator/team-flow ---------> lifecycle state in plans/<feature>/
```

## Layer Breakdown

```text
Host layer
  Claude Code, Codex, CLI
       |
       v
CLI layer
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
Packaged assets
  core/prompts/
  core/agents/
  core/templates/
  adapters/claude-code/
  adapters/codex/
       |
       v
Runtime/project state
  orchestrator/
  pathly/hooks/
  plans/<feature>/
```

## Key Design Decisions

### Decision 1: Package resources before setup
- **Options considered:** build setup first, keep repo-relative links, or add a
  resource contract first.
- **Chosen:** Add package resources first.
- **Rationale:** Setup cannot be reliable until Pathly can find its own assets
  from an installed wheel.

### Decision 2: Setup defaults to report mode
- **Options considered:** mutate by default, prompt interactively, or report by
  default with explicit `--apply`.
- **Chosen:** Report by default with explicit `--apply`.
- **Rationale:** Users should see host detection, planned writes, hook
  registration, conflicts, and final commands before Pathly changes files.

### Decision 3: Versioned user data adapter snapshots
- **Options considered:** register adapters directly from the package install
  location, keep source-checkout junctions, or copy versioned snapshots into
  user data.
- **Chosen:** Copy versioned snapshots into user data.
- **Rationale:** Snapshots make repair, inspection, rollback, and host
  registration clearer than depending on package internals or local clones.

### Decision 4: Setup is not workflow authority
- **Options considered:** let setup repair workflow state, let hooks advance
  state, or keep lifecycle routing under the orchestrator.
- **Chosen:** Keep lifecycle routing under the orchestrator.
- **Rationale:** Filesystem/FSM authority is Pathly's core product distinction.
  Setup should install surfaces, not move feature work forward.

### Decision 5: Hooks remain bounded guardrails
- **Options considered:** use hooks to drive workflow automation, or keep hooks
  deterministic and small.
- **Chosen:** Keep hooks deterministic and small.
- **Rationale:** Hidden hook-driven workflows would make Pathly harder to
  inspect, recover, and trust.

## New Command Names

- `pathly --version`
- `pathly setup`
- `pathly setup --dry-run`
- `pathly setup --apply`
- `pathly setup claude --dry-run`
- `pathly setup codex --dry-run`
- `pathly setup claude --apply`
- `pathly setup codex --apply`
- `pathly setup --repair`
- `pathly setup --force`
- `pathly status [feature]`

## Target Module Design

| Module | Responsibility |
|---|---|
| `pathly/resources.py` | Read/copy packaged prompts, templates, agents, and adapter assets. |
| `pathly/setup/locations.py` | Resolve user data, host config, and project state locations. |
| `pathly/setup/detect.py` | Detect supported host tools and host-specific availability. |
| `pathly/setup/plan.py` | Build a dry-run/apply action plan with conflicts and start commands. |
| `pathly/setup/materialize.py` | Copy/repair/force Pathly-owned adapter assets safely. |
| `pathly/cli/setup_command.py` | Render setup reports and apply setup plans. |
| `pathly/cli/status_command.py` | Summarize feature state, feedback blockers, and next actions. |

## Risks

- **`data-files` is not enough for resource APIs:** Prefer package-resource
  tests that inspect built artifacts and installed behavior.
- **CLI manager grows too large:** Keep `manager.py` as parser/dispatch wiring
  and move setup/status behavior into command modules.
- **Setup overwrites user files:** Require dry run, Pathly-owned detection,
  repair, and force semantics.
- **Host docs drift from behavior:** Add static docs tests and keep host smoke
  evidence in release readiness docs.
- **Hooks become hidden automation:** Test that hooks do not edit source or
  advance lifecycle state.
