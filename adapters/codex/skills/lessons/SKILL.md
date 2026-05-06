---
name: lessons
description: Codex-safe Pathly lessons wrapper. Promote repeated retrospective learnings into active Pathly memory.
argument-hint: ""
---

# lessons

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/lessons.md`.

## Run

# you are at adapters/codex/skills/lessons/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly lessons ...` or `Use Pathly lessons ...`.
1. Read `core/prompts/lessons.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
