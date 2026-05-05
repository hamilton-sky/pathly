---
name: bmad-import
description: Codex-safe Pathly BMAD import wrapper. Read a BMAD PRD and generate Pathly plan files.
argument-hint: "<feature-name> <prd.md> [lite|standard|strict]"
---

# bmad-import

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/bmad-import.md`.

## Run

1. Read `core/prompts/bmad-import.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
