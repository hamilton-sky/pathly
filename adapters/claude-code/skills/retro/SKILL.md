---
name: retro
description: Run a retrospective on a completed feature plan. Reads PROGRESS.md and CONVERSATION_PROMPTS.md, asks 3 focused questions, and writes RETRO.md to feed future storm sessions.
argument-hint: "[plan-folder-name, e.g., add-saucedemo-checkout]"
model: haiku
---

# retro

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/retro.md.

## Run

1. Read core/prompts/retro.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
