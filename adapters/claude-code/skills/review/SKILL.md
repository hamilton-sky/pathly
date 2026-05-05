---
name: review
description: Review code changes against project architectural rules and conventions. Reads ARCHITECTURE_PROPOSAL.md and .claude/rules/ to check for violations. Works with any project.
argument-hint: "[file-path | 'staged' | 'last']"
---

# review

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/review.md.

## Run

# you are at adapters/claude-code/skills/review/SKILL.md.

0. User runs `/pathly review` or `/path review` (or the legacy `review`) with an argument describing the file to review. This can be a specific file path, the keyword 'staged' to review all staged changes, or 'last' to review the last commit.
1. Read `pathly/core/prompts/review.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
