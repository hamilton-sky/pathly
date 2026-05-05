---
name: archive
description: Archive a completed feature plan by moving plans/<feature>/ to plans/.archive/<feature>/. Requires RETRO.md to exist and all conversations to be DONE. Recoverable via git.
argument-hint: "<feature-name>"
model: haiku
---

# archive

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/archive.md.

## Run

1. Read core/prompts/archive.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
