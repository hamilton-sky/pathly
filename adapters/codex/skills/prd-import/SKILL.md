---
name: prd-import
description: Codex-safe Pathly PRD import wrapper. Convert a PRD into Pathly plan files.
argument-hint: "<feature-name> <prd.md> [lite|standard|strict]"
---

# prd-import

This is a Codex adapter wrapper. The canonical workflow lives in `../../core/prompts/prd-import.md`.

## Run

# you are at adapters/codex/skills/prd-import/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly prd-import ...` or `Use Pathly prd-import ...`.
1. Read `../../core/prompts/prd-import.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
