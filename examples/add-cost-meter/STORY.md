# Example: add-cost-meter

This folder contains historical plan files used to implement cost tracking for
the pipeline: improvement #3 from the internal system review.

## What Happened

The retro stage had no visibility into how expensive a pipeline run was. Agents
ran, tokens accumulated, and the final retrospective did not expose cost. The
feature added cost metadata to runtime events and taught the retro workflow how
to summarize that data.

The feature was small enough to fit in a single builder conversation. The rigor
escalator found no cross-layer dependencies and no risk keywords, so the plan
stayed at lite with four core files.

In the current repository layout, shared retro behavior lives in
`core/prompts/retro.md` and adapter wrappers live under
`adapters/*/skills/retro/`.

## What This Demonstrates

- Lite rigor in practice: four files, one conversation, low overhead.
- The escalator staying quiet when there is nothing to escalate.
- A complete pipeline run from plan to build to review to test to retro.
- How `PROGRESS.md` tracks state so a run can be paused and resumed.

To see the current standard-rigor file set, inspect the templates under
`core/templates/plan/`.
