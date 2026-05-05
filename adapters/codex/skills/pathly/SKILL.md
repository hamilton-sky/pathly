---
name: pathly
description: Codex-safe Pathly entry point. Route natural-language Pathly requests such as "Use Pathly help", "Use Pathly doctor", "Use Pathly to debug...", or "Use Pathly flow..." to the right Pathly workflow without relying on Codex slash commands.
argument-hint: "[help|doctor|debug|explore|flow|review|continue|plan|build|archive|lessons|verify-state|plain English request]"
---

# Pathly for Codex

This is the Codex adapter wrapper for the tool-agnostic `core/prompts/pathly.md`
entry point.

## Run

1. Read `core/prompts/pathly.md`.
2. Follow that prompt as the source of truth for this workflow.
3. Use natural-language Codex guidance instead of plugin-defined slash commands.
4. Do not add Claude-only model frontmatter in Codex wrappers.

Codex users should invoke this skill with natural language, for example:

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
Use Pathly doctor                       -> Pathly doctor workflow
Use Pathly to debug checkout fails      -> debug workflow
Use Pathly to explore auth flow         -> explore workflow
Use Pathly flow for checkout-flow       -> team-flow checkout-flow
Use Pathly continue checkout-flow       -> team-flow checkout-flow build
Use Pathly review                       -> review workflow
Use Pathly to add password reset        -> director workflow
Use Pathly plan checkout-flow standard  -> plan workflow
Use Pathly verify-state checkout-flow   -> verify-state workflow
```

Before starting a route, print a one-sentence summary of the chosen action.
