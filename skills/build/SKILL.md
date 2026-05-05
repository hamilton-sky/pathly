---
name: build
description: Execute the next incomplete conversation of a feature plan. Reads CONVERSATION_PROMPTS.md, checks PROGRESS.md, and implements the next TODO conversation with verification. Supports auto-flow mode (execute → commit → guide to next conv).
argument-hint: "[plan-folder-name, e.g., refactor-main]"
model: sonnet
---

# build

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/build.md.

## Run

1. Read core/prompts/build.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
