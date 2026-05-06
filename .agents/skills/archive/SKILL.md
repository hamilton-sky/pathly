---
name: archive
description: Codex-safe Pathly archive wrapper. Archive a completed feature plan using the canonical Pathly archive workflow.
argument-hint: "[feature-name]"
---

# archive

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/archive.md`.

## Run

# you are at adapters/codex/skills/archive/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly archive ...` or `Use Pathly archive ...`.
1. Read `core/prompts/archive.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
