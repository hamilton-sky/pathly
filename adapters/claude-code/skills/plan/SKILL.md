---
name: plan
description: Plan a new feature. Standard and strict rigor create the full 8-file plan. Lite rigor creates the 4 files required by build: USER_STORIES.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, and CONVERSATION_PROMPTS.md.
argument-hint: "[feature-name] [lite|standard|strict]"
model: opus
---

# plan

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/plan.md.

## Run

1. Read core/prompts/plan.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
