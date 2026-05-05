---
name: review
description: Review code changes against project architectural rules and conventions. Reads ARCHITECTURE_PROPOSAL.md and .claude/rules/ to check for violations. Works with any project.
argument-hint: "[file-path | 'staged' | 'last']"
---

# review

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/review.md.

## Run

1. Read core/prompts/review.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
