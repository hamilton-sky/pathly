# clean-filesystem - Flow Diagram

## Happy Path: Clean Repository Shape

```text
[Conv 1: entrypoints]
        |
        v
[pathly/cli/ + pathly/team_flow/ canonical]
        |
        v
[Conv 2: runner interface]
        |
        v
[pathly/runners/base.py]
        |
        +--> [claude runner: usage compatible]
        |
        +--> [codex runner: stdout/stderr + empty usage fallback]
        |
        v
[Conv 3: hooks runtime]
        |
        v
[pathly/hooks/ + pathly hooks CLI]
        |
        v
[Conv 4: verified cleanup]
        |
        v
[delete legacy files or add mirror generation/check]
        |
        v
[packaging gate: build + artifact checks]
```

## Fallback Flow: Cleanup Blocked

```text
[legacy path scheduled for deletion]
        |
        v
[rg finds runtime/test/doc reference]
        |
        +--> [reference is migrated safely]
        |          |
        |          v
        |     [run targeted verify + pytest -q]
        |
        +--> [reference cannot be migrated in scope]
                   |
                   v
             [defer deletion and report blocker]
```

## Fallback Flow: Codex Usage Metadata Unavailable

```text
[codex runner executes command]
        |
        v
[stdout/stderr captured]
        |
        v
[no stable machine-readable usage]
        |
        v
[RunnerResult.usage = {}]
        |
        v
[FSM receives returncode + output safely]
```

## Component Legend

| Component | Meaning |
|-----------|---------|
| `pathly/cli/` | Canonical CLI package and console entrypoint target |
| `pathly/team_flow/` | Canonical team-flow runtime package |
| `orchestrator/` | Deterministic FSM core retained as a package |
| `pathly/runners/` | Host-neutral runner contract and implementations |
| `pathly/hooks/` | Portable hook behavior callable by CLI or runtime |
| `core/` | Installed instruction assets: prompts, agents, templates |
| `adapters/` | Installed host adapter assets and plugin metadata |
