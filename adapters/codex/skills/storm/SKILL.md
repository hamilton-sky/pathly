---
name: storm
description: Codex-safe Pathly storm wrapper. Brainstorm features, concepts, flows, and architecture approaches.
argument-hint: "[topic]"
---

# storm

This is a Codex adapter wrapper. The canonical workflow lives in `../../core/prompts/storm.md`.

## Run

# you are at adapters/codex/skills/storm/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly storm ...` or `Use Pathly storm ...`.
1. Read `../../core/prompts/storm.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
