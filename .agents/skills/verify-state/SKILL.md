---
name: verify-state
description: Codex-safe Pathly verify-state wrapper. Check stale feedback, progress drift, and dead plan references.
argument-hint: "[feature-name]"
---

# verify-state

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/verify-state.md`.

## Run

# you are at adapters/codex/skills/verify-state/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly verify-state ...` or `Use Pathly verify-state ...`.
1. Read `core/prompts/verify-state.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
