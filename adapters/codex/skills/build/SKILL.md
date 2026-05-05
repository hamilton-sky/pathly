---
name: build
description: Codex-safe Pathly build wrapper. Execute the next incomplete conversation for a feature plan.
argument-hint: "[feature-name]"
---

# build

This is a Codex adapter wrapper. The canonical workflow lives in `../../core/prompts/build.md`.

## Run

# you are at adapters/codex/skills/build/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly build ...` or `Use Pathly build ...`.
1. Read `../../core/prompts/build.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
