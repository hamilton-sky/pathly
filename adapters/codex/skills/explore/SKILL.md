---
name: explore
description: Codex-safe Pathly explore wrapper. Trace a codebase question and report findings without building.
argument-hint: "<question>"
---

# explore

This is a Codex adapter wrapper. The canonical workflow lives in `../../core/prompts/explore.md`.

## Run

# you are at adapters/codex/skills/explore/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly explore ...` or `Use Pathly explore ...`.
1. Read `../../core/prompts/explore.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
