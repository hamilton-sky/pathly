# pathly-engine

External CLI for reading and advancing Pathly workflow state from a plain terminal, without opening Claude Code or Codex.

## Install

```bash
pip install -e pathly-engine/
```

## Usage

```bash
pathly go "add password reset"    # record intent; prints current state and next step
pathly status                     # show current FSM state and suggested next action
pathly status <feature>           # show state for a specific feature
pathly doctor                     # diagnose: engine installed, plans/ accessible, STATE.json and EVENTS.jsonl readable
```

## What Each Command Does

**`pathly go "<intent>"`** — writes a `COMMAND` event to `EVENTS.jsonl` and prints the current state plus the suggested next action. Does not spawn agents or advance the FSM.

**`pathly status [feature]`** — reads `STATE.json` and `EVENTS.jsonl` for the most recently active feature (or the named feature) and prints a summary table with the current state, rigor level, last actor, event count, and a suggested next action.

**`pathly doctor`** — runs four checks and prints `[PASS]` / `[FAIL]` for each:
- engine installed
- plans/ accessible
- STATE.json readable
- EVENTS.jsonl readable

## Notes

- The CLI does **not** spawn Claude, Codex, or any AI agent. It writes filesystem state that a human or AI tool reads later.
- `doctor` never advances workflow state.
- Both projects (`pathly-adapters` and `pathly-engine`) are independent. Installing one does not require the other.

## Release Status

Public beta. `go`, `status`, and `doctor` are verified. Advanced orchestration commands are managed through the Claude Code or Codex adapters.
