---
name: path
description: Short alias for the Pathly entry point. Route /path help, doctor, debug, explore, flow, review, continue, plan, build, archive, lessons, imports, verify-state, or plain-English requests exactly like /pathly.
argument-hint: "[help|doctor|debug|explore|flow|review|continue|plan|build|archive|lessons|verify-state|plain English request]"
---

# path

This skill is an adapter-facing wrapper. The canonical workflow lives in core/prompts/path.md.

## Run

1. Read core/prompts/path.md.
2. Follow that prompt as the source of truth for this workflow.
3. Preserve the slash-command contract from this skill's frontmatter.
4. Prefer /pathly ... or /path ... in user-facing guidance; treat legacy direct skill names as compatibility aliases.
