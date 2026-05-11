# add-cost-meter - Implementation Plan

## Phases

### Phase 1 - Add Cost Data To Event Logging

**File:** `orchestrator/eventlog.py`

**Change:** Record token and cost metadata on agent completion events. Cost data
must remain append-only and recoverable through `EVENTS.jsonl`.

**Layer:** orchestrator runtime only.

### Phase 2 - Retro Reads And Surfaces Cost Summary

**File:** `core/prompts/retro.md`

**Change:** After writing `RETRO.md`, read `EVENTS.jsonl`, filter agent
completion events with cost metadata, group by agent, and summarize total cost.
If no cost data exists, skip the section or state that no cost data was
recorded.

**Adapter notes:** Claude and Codex skill wrappers load the canonical retro
prompt from `core/prompts/retro.md`. Do not edit historical `skills/retro/`
paths; that directory is not part of the current repository layout.

## Architecture Notes

- Cost records are append-only.
- Missing cost data is valid.
- Retro is the only current consumer.
- No dashboard or webhook is in scope.

## Conversation Breakdown

One conversation covers both phases.

Verify with:

```text
python -m pytest tests/ -q
```
