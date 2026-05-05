# Pathly Orchestrator

This folder contains the executable filesystem state-machine runtime for
Pathly.

It should stay outside `core/`.

## Boundary

`orchestrator/` owns Python runtime behavior:

- FSM state objects
- event definitions
- reducer transitions
- event log persistence
- recovery from `EVENTS.jsonl` and `STATE.json`

`core/` owns tool-agnostic contracts and content:

- prompts
- workflow descriptions
- agent contracts
- reusable templates

The core prompts may reference `orchestrator/` APIs, but the Python runtime code
should remain importable as the top-level `orchestrator` package. The CLI and
tests already import it this way.

## Current Files

- `constants.py`: FSM states, agent names, feedback files, modes, and event names
- `events.py`: event dataclasses consumed by the reducer
- `state.py`: serializable FSM state object
- `reducer.py`: pure transition logic
- `eventlog.py`: append-only event log and state recovery
- `utils.py`: shared runtime helpers

Do not move this folder into `core/` unless the Python package/import contract is
intentionally redesigned.
