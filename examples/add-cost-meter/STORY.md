# Example: add-cost-meter

This folder contains the actual plan files used to implement cost tracking for the pipeline — improvement #3 from the internal system review.

## What happened

The retro stage had no visibility into how expensive a pipeline run actually was. Agents ran, tokens accumulated, and at the end there was no number to look at. After a few long runs where cost was unclear, the decision was to add cost tracking as a first-class concern: every agent completion appends a cost event to `EVENTS.jsonl`, and the retro skill surfaces a summary.

The feature was small enough to fit in a single builder conversation. The rigor escalator ran and detected no cross-layer dependencies and no risk keywords — so the plan stayed at lite (4 files). No escalation was offered, no extra files were added. The builder touched 2 files (`orchestrator/eventlog.py` and `skills/retro/SKILL.md`), the reviewer passed on the first run, and the retro was written in under 5 minutes.

## What this demonstrates

- Lite rigor in practice: 4 files, 1 conversation, no ceremony overhead
- The escalator correctly staying quiet when there's nothing to escalate
- A complete pipeline run from plan → build → review → test → retro
- How `PROGRESS.md` tracks state so a run can be paused and resumed

To see what a standard-rigor plan looks like (with ARCHITECTURE_PROPOSAL.md, EDGE_CASES.md, etc.), check `docs/SECURITY_RELIABILITY_REVIEW.md` — the FSM orchestrator was planned at standard rigor and has all 8 files.
