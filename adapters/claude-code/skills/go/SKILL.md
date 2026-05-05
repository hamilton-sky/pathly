---
name: go
description: Natural-language Director entry point. Reads project state, classifies the user's request, chooses the lightest safe workflow, and routes to the right skill while hiding pipeline details.
argument-hint: "[optional: free text description of what you want]"
---

# go

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/go.md.

## Run

# you are at adapters/claude-code/skills/go/SKILL.md.

0. User runs `/pathly go` or `/path go` (or the legacy `go`) with an optional free-text argument describing their request.
1. Read `pathly/core/prompts/go.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
