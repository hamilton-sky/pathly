---
name: meet
description: Consult one relevant Pathly role during an active feature flow. Read-only advice only; writes a consult note and offers explicit promotion back to planner or architect.
argument-hint: "[feature-name]"
model: haiku
---

# meet

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/meet.md.

## Run

# you are at adapters/claude-code/skills/meet/SKILL.md.

0. User runs `/pathly meet` or `/path meet` with an optional feature name argument.
1. Read `pathly/core/prompts/meet.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
5. Keep the consultation read-only. Do not edit code or silently update workflow state.
