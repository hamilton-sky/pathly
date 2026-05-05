---
name: plan
description: Codex-safe Pathly plan wrapper. Create or extend a feature plan using lite, standard, or strict rigor.
argument-hint: "[feature-name] [lite|standard|strict]"
---

# plan

This is a Codex adapter wrapper. The canonical workflow lives in `core/prompts/plan.md`.

## Run

# you are at adapters/codex/skills/plan/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly plan ...` or `Use Pathly plan ...`.
1. Read `core/prompts/plan.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter to this Codex wrapper.
5. Do not satisfy this route by running the `pathly` CLI unless the user explicitly asks for the CLI fallback.
