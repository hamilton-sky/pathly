# Pathly Core

This folder is the tool-agnostic source of truth for Pathly.

Core files describe what Pathly knows and how the workflows behave. They should
not depend on Claude Code slash-command syntax, Codex plugin metadata, or any
other host-specific packaging format.

Adapters turn this core into tool-specific experiences:

- Claude Code commands and skills
- Codex plugin skills
- CLI commands
- future Cursor, Windsurf, BMAD, or generic prompt packs

Current status: this is an additive scaffold. The existing `agents/` and
`skills/` folders still power the working plugin while the core is filled in.
