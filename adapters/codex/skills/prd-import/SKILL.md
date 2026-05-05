---
name: prd-import
description: Codex-safe Pathly PRD import wrapper. Convert a PRD into Pathly plan files.
argument-hint: "<feature-name> <prd.md> [lite|standard|strict]"
---

# prd-import

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/prd-import.md`.

## Run

1. Read `core/prompts/prd-import.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
