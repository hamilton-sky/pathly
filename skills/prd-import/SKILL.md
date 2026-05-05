---
name: prd-import
description: Read any PRD file (from BMAD, hand-written, or AI-generated) and generate plan files in plans/<feature>/. Lite creates 4 required files; standard/strict create all 8 files.
argument-hint: "<feature-name> <path/to/PRD.md> [lite|standard|strict]  — e.g., hotel-search docs/hotel-search-prd.md strict"
model: opus
---

# prd-import

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/prd-import.md.

## Run

1. Read core/prompts/prd-import.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
