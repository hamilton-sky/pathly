---
name: pathly
description: Codex-safe Pathly entry point. Route natural-language Pathly requests such as "Pathly help", "Pathly doctor", "Pathly add password reset", "Use Pathly to debug...", or "Use Pathly flow..." to the right Pathly workflow without relying on Codex slash commands.
argument-hint: "[help|doctor|debug|explore|flow|review|continue|plan|build|archive|lessons|verify-state|plain English request]"
---

# Pathly for Codex

This is the Codex adapter wrapper for the tool-agnostic `../../core/prompts/pathly.md`
entry point.

## Run

# you are at adapters/codex/skills/pathly/SKILL.md.

0. User invokes this skill with natural language, such as `Pathly help`, `Pathly add password reset`, or `Use Pathly to debug checkout fails`.
1. Read `../../core/prompts/pathly.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter in Codex wrappers.
5. Do not satisfy Pathly routes by running the `pathly` CLI unless the user
   explicitly asks for the CLI fallback. Prefer the corresponding
   `../../core/prompts/*.md` workflow.
6. Treat route strings in core prompts as workflow identifiers. For example,
   `team-flow checkout-flow build` means continue the team-flow behavior for
   that feature in Codex; it does not mean execute a shell command.

Codex users should invoke this skill with natural language. Short forms should
work when Codex recognizes the Pathly skill:

```text
Pathly help
Pathly doctor
Pathly add password reset
Pathly debug checkout button does nothing
Pathly explore how auth state flows
Pathly flow checkout-flow
```

The more explicit forms are useful when Codex does not confidently select the
plugin skill:

```text
Use Pathly help
Use Pathly doctor on this project
Use Pathly to add password reset
Use Pathly to debug checkout button does nothing
Use Pathly to explore how auth state flows
Use Pathly flow for checkout-flow
```

Do not tell Codex users to type `/pathly ...` or `/path ...` unless Codex adds
support for plugin-defined slash commands. Current Codex builds reserve slash
commands for Codex UI commands.

## Route

- `help`: run the Pathly help workflow.
- `doctor`: run Pathly doctor diagnostics.
- `debug <symptom>`: run the debug workflow.
- `explore <question>`: run the explore workflow.
- `flow <feature>` or `run <feature>`: run the team-flow workflow.
- `continue <feature>`: resume team-flow build for that feature.
- `review`: run the review workflow.
- any root skill name: run that skill with the remaining text as arguments.
- anything else: route through the director workflow as a plain-English request.

## Invocation Mapping

When choosing a route, behave exactly as if the user had requested the
corresponding existing Pathly skill:

```text
Use Pathly help                         -> Pathly help workflow
Pathly help                             -> Pathly help workflow
Use Pathly doctor                       -> Pathly doctor workflow
Pathly doctor                           -> Pathly doctor workflow
Use Pathly to debug checkout fails      -> debug workflow
Pathly debug checkout fails             -> debug workflow
Use Pathly to explore auth flow         -> explore workflow
Pathly explore auth flow                -> explore workflow
Use Pathly flow for checkout-flow       -> team-flow checkout-flow
Pathly flow checkout-flow               -> team-flow checkout-flow
Use Pathly continue checkout-flow       -> team-flow checkout-flow build
Use Pathly review                       -> review workflow
Pathly review                           -> review workflow
Use Pathly to add password reset        -> director workflow
Pathly add password reset               -> director workflow
Use Pathly plan checkout-flow standard  -> plan workflow
Use Pathly verify-state checkout-flow   -> verify-state workflow
```

Before starting a route, print a one-sentence summary of the chosen action.
