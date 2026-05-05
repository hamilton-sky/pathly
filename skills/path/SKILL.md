---
name: path
description: Short alias for the Pathly entry point. Route /path help, doctor, debug, explore, flow, review, continue, plan, build, archive, lessons, imports, verify-state, or plain-English requests exactly like /pathly.
argument-hint: "[help|doctor|debug|explore|flow|review|continue|plan|build|archive|lessons|verify-state|plain English request]"
---

# Path

Use this skill as the short slash-command alias for Pathly.

`/path` is equivalent to `/pathly`. Keep `/pathly` as the canonical command in
formal docs and examples, but accept `/path` for day-to-day use across supported
slash-command frameworks.

## Route

Follow the same routing behavior as `skills/pathly/SKILL.md`:

- `help`: run the Pathly help workflow.
- `doctor`: run Pathly doctor diagnostics.
- `debug <symptom>`: run the debug workflow.
- `explore <question>`: run the explore workflow.
- `flow <feature>` or `run <feature>`: run the team-flow workflow.
- `continue <feature>`: resume team-flow build for that feature.
- `review`: run the review workflow.
- any root skill name: run that skill with the remaining text as arguments.
- anything else: route through the director workflow as a plain-English request.

Before starting a route, print a one-sentence summary of the chosen action.
