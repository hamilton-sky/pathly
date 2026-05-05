---
name: pathly
description: Codex-safe Pathly entry point. Route /pathly help, doctor, debug, explore, flow, review, continue, or plain-English requests to the right Pathly workflow without using Codex built-in /help.
argument-hint: "[help|doctor|debug|explore|flow|review|continue|plain English request]"
---

# Pathly for Codex

This is the Codex adapter wrapper for the tool-agnostic `core/prompts/pathly.md`
entry point.

Codex users should type `/pathly ...` instead of `/help`, `/go`, `/debug`, or
`/explore` so Pathly does not collide with Codex built-in commands.

## Route

- `help`: run the Pathly help workflow.
- `doctor`: run Pathly doctor diagnostics.
- `debug <symptom>`: run the debug workflow.
- `explore <question>`: run the explore workflow.
- `flow <feature>` or `run <feature>`: run the team-flow workflow.
- `continue <feature>`: resume team-flow build for that feature.
- `review`: run the review workflow.
- anything else: route through the director workflow as a plain-English request.

## Invocation Mapping

When choosing a route, behave exactly as if the user had requested the
corresponding existing Pathly skill:

```text
/pathly help                         -> Pathly help workflow
/pathly doctor                       -> Pathly doctor workflow
/pathly debug checkout fails         -> debug workflow
/pathly explore auth flow            -> explore workflow
/pathly flow checkout-flow           -> team-flow checkout-flow
/pathly continue checkout-flow       -> team-flow checkout-flow build
/pathly review                       -> review workflow
/pathly add password reset           -> director workflow
```

Before starting a route, print a one-sentence summary of the chosen action.
