# Parallel Lanes — Future Design Note

_Deferred from storm session on production-readiness-hardening_

## What this is

A "parallel lane" means two or more manager processes running simultaneously against the
same feature — each driving a different workstream (e.g. frontend builder + backend builder)
and both writing to the same EVENTS.jsonl.

This is NOT how pathly works today and is NOT in scope for this hardening work.
This file captures the design problem so the conversation isn't lost.

## Why it doesn't exist yet

Today, agents are children of the manager — subprocesses spawned sequentially:

```
manager (one process)
    │
    ├──► builder  (subprocess, exits when done)
    ├──► reviewer (subprocess, exits when done)
    └──► tester   (subprocess, exits when done)
```

The manager is the single writer of EVENTS.jsonl. Agents never touch the event log.
"Multiple areas" means multiple features (each with their own directory), not multiple managers.

## What parallel lanes would require

```
HYPOTHETICAL: two managers, one feature

manager-A (frontend lane) ──┐
                             ├──► plans/my-feature/EVENTS.jsonl (shared)
manager-B (backend lane)  ──┘
```

For this to work without corruption, the following must be true:

1. **Concurrent-safe event log** — O_APPEND alone is not enough across two processes.
   Options: file lock (fcntl/lockfile), SQLite WAL mode, or a coordinator process.

2. **Reducer must handle interleaved events** — the pure FSM currently assumes a single
   ordered event stream. Parallel lanes produce two interleaved streams. The reducer
   would need to distinguish lane-scoped events from global events.

3. **State must be lane-aware** — STATE.json currently holds one current state.
   Parallel lanes need either: (a) one STATE.json per lane, or (b) a composite state
   object with per-lane substates.

4. **Feedback files must be lane-scoped** — REVIEW_FAILURES.md written by lane A
   should not block lane B.

5. **Merge / sync points** — lanes must be able to signal "lane ready to merge" and
   the orchestrator must coordinate the join.

## Recommended approach when the time comes

Don't extend the current single-manager FSM. Instead:

```
Option: Coordinator + worker model

  coordinator (thin orchestrator)
      │
      ├──► lane-manager-A ──► plans/my-feature/lanes/frontend/
      └──► lane-manager-B ──► plans/my-feature/lanes/backend/

  Each lane is an independent feature directory.
  Coordinator writes merge events to plans/my-feature/EVENTS.jsonl.
```

This keeps each lane's FSM pure and single-process, avoids shared-writer problems,
and lets the coordinator handle sync points at the feature level.

## Decision

**Deferred.** The current lockfile (one manager per feature) is the right constraint now.
If parallel lanes become a requirement, open a new exploration: `explore parallel-lanes`.
