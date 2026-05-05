---
name: team-flow
description: Codex-safe Pathly team-flow wrapper. Run the full feature pipeline with discovery, planning, build, review, test, and retro stages.
argument-hint: "<feature-name> [lite|standard|strict] [fast] [discovery|plan|build|test]"
---

# team-flow

This is a Codex adapter wrapper. The canonical workflow lives in `../../core/prompts/team-flow.md`.

## Run

# you are at adapters/codex/skills/team-flow/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly team-flow ...` or `Use Pathly team-flow ...`.
1. Read `../../core/prompts/team-flow.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
6. If the workflow needs a subagent role, use Codex-native delegation when available or continue with the role instructions from `core/agents/`; do not require the `claude` CLI.
