# add-cost-meter - Conversation Guide

One conversation. Produces runnable, tested code.

## Conversation 1: Cost Events And Retro Summary

**Stories delivered:** S1.1, S1.2

```text
Implement add-cost-meter Conversation 1 from examples/add-cost-meter/IMPLEMENTATION_PLAN.md.

Scope:
- Record cost metadata in the event log path used by Pathly runtime events.
- Update the canonical retro workflow in core/prompts/retro.md so retros can
  summarize cost data from EVENTS.jsonl.
- Keep adapter wrappers thin. Do not duplicate retro logic in
  adapters/claude-code/skills/retro/SKILL.md or adapters/codex/skills/retro/SKILL.md.

Layer rules:
- Runtime persistence belongs in orchestrator/.
- Shared workflow instructions belong in core/prompts/.
- Host-specific wrapper files should only point at core prompts.

Verify:
python -m pytest tests/ -q

After verification, update examples/add-cost-meter/PROGRESS.md Conv 1 to DONE.
```

**Expected output:** runtime events can carry cost metadata and the retro
workflow documents how to summarize it.

**Files touched:** `orchestrator/eventlog.py`, `core/prompts/retro.md`
