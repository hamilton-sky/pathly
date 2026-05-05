# Pathly Adapters

Adapters package the Pathly core for specific tools.

The adapter should be thin:

- add tool-specific metadata
- choose command names that avoid conflicts
- install files in the format the host tool expects
- keep workflow behavior in `core/`

Current adapters:

- `claude-code/`: Claude Code slash-command and plugin packaging
- `codex/`: Codex plugin packaging with `/pathly` as the safe front door
- `cli/`: terminal command contract for `pathly`
