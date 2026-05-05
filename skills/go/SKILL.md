---
name: go
description: Natural-language Director entry point. Reads project state, classifies the user's request, chooses the lightest safe workflow, and routes to the right skill while hiding pipeline details.
argument-hint: "[optional: free text description of what you want]"
---

# go

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/go.md.

## Run

1. Read core/prompts/go.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
