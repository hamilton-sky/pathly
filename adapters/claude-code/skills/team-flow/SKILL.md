---
name: team-flow
description: Full feature pipeline with feedback loops — discovery → plan → (implement → review → fix?) × N → test → (fix?) → retro. Standard/strict review every conversation; lite can review final-only. Feedback files route issues to the right agent automatically. Add 'lite', 'standard', or 'strict' to choose rigor. Add 'fast' to skip pause points outside strict mode. Add 'build', 'plan', or 'test' to enter mid-pipeline.
argument-hint: "<feature-name> [lite|standard|strict|nano] [fast] [plan|build|test]"
---

# team-flow

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/team-flow.md.

## Run

# you are at adapters/claude-code/skills/team-flow/SKILL.md.

0. User runs `/pathly team-flow` or `/path team-flow` (or the legacy `team-flow`) with arguments describing the feature, rigor level, and pipeline stage.
1. Read `pathly/core/prompts/team-flow.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
