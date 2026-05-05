---
name: debug
description: Dedicated bug-investigation pipeline — scout traces the symptom, builder fixes it, tester verifies before and after. FSM states extend IDLE through DONE without touching the main team-flow pipeline.
argument-hint: "<symptom-name>"
---

# debug

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/debug.md.

## Run

# you are at adapters/claude-code/skills/debug/SKILL.md.

0. User runs `/pathly debug` or `/path debug` (or the legacy `debug`) with a free-text argument describing the symptom they want to debug.
1. Read `pathly/core/prompts/debug.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
