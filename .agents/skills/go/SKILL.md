---
name: go
description: Codex-safe Pathly director wrapper. Classify a plain-English request and route it to the lightest safe Pathly workflow.
argument-hint: "<request>"
---

# go

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/go.md`.

## Run

# you are at adapters/codex/skills/go/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly add password reset` or `Use Pathly go ...`.
1. Read `core/prompts/go.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
6. When `core/prompts/go.md` chooses a route such as `storm <topic>` or `team-flow <feature> lite`, translate it into Codex skill behavior, not a shell command.
