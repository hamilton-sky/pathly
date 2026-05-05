# Pathly Adapters

Adapters package the Pathly core for specific tools.

The adapter should be thin:

- add tool-specific metadata
- expose `/pathly ...` as the canonical command and `/path ...` as the short alias
- keep legacy command names only as compatibility aliases when needed
- install files in the format the host tool expects
- keep workflow behavior in `core/`

Adapters should not become the source of truth for Pathly behavior. If a prompt,
workflow contract, agent role, or plan template can be shared across tools, put
it under `core/` first and let the adapter reference or package it.

Current adapters:

- `claude-code/`: Claude Code slash-command and plugin packaging with `/pathly` and `/path`
- `codex/`: Codex plugin packaging with `/pathly` and `/path` as safe front doors
- `cli/`: terminal command contract for `pathly`
