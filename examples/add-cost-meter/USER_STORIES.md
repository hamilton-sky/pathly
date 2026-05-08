# add-cost-meter — User Stories

## Context
After a pipeline run, there was no way to know how many tokens the run consumed or what it cost. Developers had to check their Anthropic dashboard manually. This feature adds cost tracking directly into the pipeline: each agent completion records token usage, and the retro skill prints a cost summary.

## Stories

### Story 1.1: Cost events recorded per agent
**As a** developer running a pipeline, **I want** each agent completion to append a cost event to `EVENTS.jsonl`, **so that** I have a machine-readable record of what each stage cost.

**Acceptance Criteria:**
- [ ] `EventLog.append_cost(agent, input_tokens, output_tokens, cost_usd)` exists
- [ ] Each agent completion in team-flow appends a cost event
- [ ] The event includes: agent name, timestamp, input_tokens, output_tokens, cost_usd

**Edge Cases:**
- If token counts are unavailable (API response missing usage field): log `cost_usd = null`, do not block the pipeline

**Delivered by:** Phase 1 → Conversation 1

### Story 1.2: Retro surfaces cost summary
**As a** developer reviewing a completed pipeline run, **I want** the retro to print a cost summary, **so that** I know how much the run cost without leaving the terminal.

**Acceptance Criteria:**
- [ ] Retro workflow reads `EVENTS.jsonl` and sums cost events by agent
- [ ] Retro output includes a cost table: agent | conversations | total_usd
- [ ] If no cost events exist: retro skips the cost section without error

**Edge Cases:**
- If `EVENTS.jsonl` is missing or empty: skip cost section, print a note

**Delivered by:** Phase 2 → Conversation 1
