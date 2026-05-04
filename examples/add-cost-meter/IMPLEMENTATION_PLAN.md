# add-cost-meter — Implementation Plan

## Phases

### Phase 1 — Add cost event to EventLog
**File:** `orchestrator/eventlog.py`
**Change:** Add `append_cost(agent, input_tokens, output_tokens, cost_usd)` method. Appends a JSON line with `type: "cost"` to `EVENTS.jsonl`.
**Layer:** orchestrator only. Do not touch skills or agents.

### Phase 2 — Retro reads and surfaces cost summary
**File:** `skills/retro/SKILL.md`
**Change:** After writing RETRO.md, read `EVENTS.jsonl`, filter `type == "cost"`, group by agent, sum `cost_usd`. Print a cost table in the retro output. If no cost events: skip silently.
**Layer:** skill layer only. Do not touch orchestrator.

## Architecture notes
- Cost events are append-only. No deletion, no correction.
- `cost_usd = null` is valid — means token info was unavailable.
- Retro is the only consumer of cost events. No dashboard, no webhook.

## Conversation breakdown
- 1 conversation covers both phases.
- Verify command: `python -m pytest tests/ -q` (or manual `python orchestrator/eventlog.py --test` if tests are not yet wired).
