---
name: verify-state
description: Consistency check — detects stale feedback files, PROGRESS.md drift from git, and plan files pointing to deleted code. Run before resuming a feature pipeline or when something feels off.
argument-hint: "[feature-name]"
---

# verify-state

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/verify-state.md.

## Run

1. Read core/prompts/verify-state.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
