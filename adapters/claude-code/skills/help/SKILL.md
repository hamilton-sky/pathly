---
name: help
description: Detect current project state and show numbered options the user can pick. Activates the chosen action immediately. Pass a feature name to get state for that feature.
argument-hint: "[feature-name]"
model: haiku
---

# help

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/help.md.

## Run

1. Read core/prompts/help.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
