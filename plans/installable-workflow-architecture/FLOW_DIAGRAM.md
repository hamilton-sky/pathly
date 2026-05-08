# installable-workflow-architecture - Flow Diagram

## Happy Path: install, setup, and use

```text
[pip install pathly]
        |
        v
[installed pathly CLI]
        |  --version / --help / doctor
        v
[pathly.resources]
        |  load packaged assets
        v
[core + adapters assets available]
        |
        v
[pathly setup --dry-run]
        |  detect hosts + planned writes
        v
[setup action plan]
        |  user reviews
        v
[pathly setup --apply]
        |  copy versioned snapshots
        v
[user data Pathly adapters]
        |
        +--> [Claude Code: /pathly ...]
        |
        +--> [Codex: Use Pathly ...]
        |
        +--> [CLI: pathly go "..."]
```

## Runtime Boundary

```text
[host request]
        |
        v
[Pathly adapter or CLI]
        |  route request
        v
[Director / pathly front door]
        |  choose workflow
        v
[orchestrator + team-flow]
        |  append event, reduce state
        v
[plans/<feature>/]
        |  STATE.json + EVENTS.jsonl + feedback
        v
[next owner/action]
```

## Setup Fallback / Error Flow

```text
[pathly setup --dry-run]
        |
        v
[detect host unavailable]
        |
        +--> [report missing host + next steps]
        |
        v
[planned target exists]
        |
        +--> [Pathly-owned?]
        |          |
        |          +--> yes: allow --repair
        |          |
        |          +--> no: require --force or stop
        |
        v
[no writes during dry run]
```

## Hook Boundary

```text
[agent writes feedback file]
        |
        v
[host hook invokes pathly hooks]
        |
        v
[validate payload + canonical path]
        |
        +--> invalid: diagnostic only
        |
        v
[classify or add metadata under plans/]
        |
        v
[return control to host]
        |
        v
[orchestrator reads files on next workflow step]
```

## Component Legend

| Component | Meaning |
|-----------|---------|
| `pathly.resources` | Host-neutral API for packaged assets. |
| `pathly setup --dry-run` | Non-mutating setup action plan. |
| `pathly setup --apply` | Explicit adapter materialization. |
| user data snapshots | Versioned copied adapter assets for host registration. |
| `orchestrator` | Lifecycle FSM authority. |
| `pathly hooks` | Bounded validation/classification guardrails. |
