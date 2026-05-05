---
name: storm
description: Brainstorming conversation mode — explore features, ideas, concepts, flows, and architecture approaches through interactive discussion with ASCII diagrams. Stays active turn-by-turn until the user says stop.
argument-hint: "[optional: topic to start brainstorming, e.g. 'agent-to-agent protocol', 'resolver cascade redesign']"
model: opus
---

# storm

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/storm.md.

## Run

# you are at adapters/claude-code/skills/storm/SKILL.md.

0. User runs `/pathly storm` or `/path storm` (or the legacy `storm`) with an optional argument describing the topic to start brainstorming.
1. Read `pathly/core/prompts/storm.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
