# Pathly Adapters

Adapters package the Pathly core for specific tools.

The adapter should be thin:

- add tool-specific metadata
- expose the host-native Pathly entry point
- keep legacy command names only as compatibility aliases when needed
- install files in the format the host tool expects
- keep workflow behavior in `core/`

Adapters should not become the source of truth for Pathly behavior. If a prompt,
workflow contract, agent role, or plan template can be shared across tools, put
it under `core/` first and let the adapter reference or package it.

Current adapters:

- `claude-code/`: Claude Code slash-command and plugin packaging with `/pathly` and `/path`
- `codex/`: Codex plugin packaging with natural-language skill prompts such as "Use Pathly help"
- `cli/`: terminal command contract for `pathly`
