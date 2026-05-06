---
name: meet
description: Codex-safe Pathly meet wrapper. Consult one relevant Pathly role during an active feature flow, write a consult note, and offer explicit return or promotion options.
argument-hint: "[feature-name]"
---

# meet

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/meet.md`.

## Run

# you are at adapters/codex/skills/meet/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly meet ...` or `Use Pathly meet ...`.
1. Read `core/prompts/meet.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
6. Keep the consultation read-only. Do not edit code or silently update workflow state.
