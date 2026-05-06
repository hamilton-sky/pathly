---
name: help
description: Codex-safe Pathly help wrapper. Detect current project state and render the canonical numbered Pathly menu with options like [1] and "See all commands"; never summarize CLI help unless the user asks for CLI fallback.
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
6. For normal help, print the numbered interactive menu from the core prompt
   (`[1] ...`, `[2] ...`, and "See all commands" where appropriate). Do not
   answer with the terse CLI shape `Plans:` / `Next:` unless CLI fallback was
   explicitly requested.
