---
name: lessons
description: Promote candidate lessons to active memory. Reads LESSONS_CANDIDATE.md and recent RETRO.md files, finds patterns that repeat across 2+ features, and writes LESSONS.md for planner consumption.
model: sonnet
---

# lessons

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/lessons.md.

## Run

# you are at adapters/claude-code/skills/lessons/SKILL.md.

0. User runs `/pathly lessons` or `/path lessons` (or the legacy `lessons`) with an optional free-text argument describing the lesson they want to promote.
1. Read `pathly/core/prompts/lessons.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
