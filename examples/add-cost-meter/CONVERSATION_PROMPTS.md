# add-cost-meter — Conversation Guide

1 conversation. Produces runnable, tested code. Commit after.

---

## Conversation 1: Cost events + retro summary (Phases 1–2)

**Stories delivered:** S1.1, S1.2

**Prompt to paste:**
```
Implement add-cost-meter Conversation 1 (Phases 1–2) from examples/add-cost-meter/IMPLEMENTATION_PLAN.md.

Scope:
- Phase 1: Add `append_cost(agent, input_tokens, output_tokens, cost_usd)` to `orchestrator/eventlog.py`.
  Appends a JSON line with `{"type": "cost", "agent": ..., "input_tokens": ..., "output_tokens": ..., "cost_usd": ..., "ts": ...}` to EVENTS.jsonl.
  `cost_usd` may be null if token info was unavailable — do not raise, just write null.
- Phase 2: Update `skills/retro/SKILL.md` to read EVENTS.jsonl after writing RETRO.md.
  Filter lines where `type == "cost"`. Group by agent. Sum `cost_usd` (skip nulls).
  Print a cost table: agent | conversations | total_usd.
  If no cost events or EVENTS.jsonl missing: skip the section, print "No cost data recorded."

Layer rules:
- Phase 1 touches orchestrator/ only.
- Phase 2 touches skills/retro/ only.
- Do NOT touch team-flow/SKILL.md, agents/, or any other file.

Verify: python -m pytest tests/ -q (or python orchestrator/eventlog.py --selftest if tests are not wired yet)
After done, update examples/add-cost-meter/PROGRESS.md Conv 1 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** `eventlog.py` has `append_cost`; retro skill prints cost table after RETRO.md.
**Files touched:** `orchestrator/eventlog.py`, `skills/retro/SKILL.md`

---
