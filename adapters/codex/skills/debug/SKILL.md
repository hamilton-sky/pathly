---
name: debug
description: Codex-safe Pathly debug wrapper. Investigate a bug, identify root cause, fix it, and verify before and after.
argument-hint: "<symptom>"
---

# debug

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/debug.md`.

## Run

# you are at adapters/codex/skills/debug/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly debug ...` or `Use Pathly debug ...`.
1. Read `core/prompts/debug.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
