---
name: pathly
description: Pathly entry point. Route /pathly or /path help, doctor, debug, explore, flow, review, continue, plan, build, archive, lessons, imports, verify-state, or plain-English requests to the right Pathly workflow.
argument-hint: "[help|doctor|debug|explore|flow|review|continue|plan|build|archive|lessons|verify-state|plain English request]"
---

# pathly

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/pathly.md.

## Run

1. Read core/prompts/pathly.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
