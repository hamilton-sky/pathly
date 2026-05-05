---
name: help
description: Codex-safe Pathly help wrapper. Detect current project state and show the next useful Pathly actions.
argument-hint: "[feature-name]"
---

# help

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/help.md`.

## Run

# you are at adapters/codex/skills/help/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly help ...` or `Use Pathly help ...`.
1. Read `core/prompts/help.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
