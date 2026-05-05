---
name: review
description: Codex-safe Pathly review wrapper. Review code changes against project architecture and conventions.
argument-hint: ""
---

# review

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/review.md`.

## Run

# you are at adapters/codex/skills/review/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly review ...` or `Use Pathly review ...`.
1. Read `core/prompts/review.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
