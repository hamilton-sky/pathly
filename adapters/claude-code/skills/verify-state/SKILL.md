---
name: verify-state
description: Consistency check — detects stale feedback files, PROGRESS.md drift from git, and plan files pointing to deleted code. Run before resuming a feature pipeline or when something feels off.
argument-hint: "[feature-name]"
---

# verify-state

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/verify-state.md.

## Run

# you are at adapters/claude-code/skills/verify-state/SKILL.md.

0. User runs `/pathly verify-state` or `/path verify-state` (or the legacy `verify-state`) with an argument describing the feature name.
1. Read `pathly/core/prompts/verify-state.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
