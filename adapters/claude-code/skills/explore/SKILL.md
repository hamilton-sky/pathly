---
name: explore
description: Exploratory investigation mode — scout traces a question through the codebase, produces structured findings, and optionally graduates into a full team-flow feature. No plan files, no acceptance criteria, no building.
argument-hint: "<topic-or-question>"
---

# explore

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/explore.md.

## Run

# you are at adapters/claude-code/skills/explore/SKILL.md.

0. User runs `/pathly explore` or `/path explore` (or the legacy `explore`) with a free-text argument describing the topic or question they want to explore.
1. Read `pathly/core/prompts/explore.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
