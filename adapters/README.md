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

## Model Metadata

Keep vendor-specific model names in adapter wrappers, not in `core/`. Core
workflows should describe model intent with portable tiers:

- `simple`: quick lookup, summarization, deterministic state checks
- `normal`: planning, implementation, review, testing, routine debugging
- `advanced`: architecture, ambiguous requirements, high-risk planning

- Claude-facing wrappers may use Claude model labels such as `haiku`, `sonnet`,
  or `opus` when mapping those tiers.
- Codex-facing wrappers should omit Claude model labels and rely on the active
  Codex session model unless Codex-specific model overrides are explicitly
  supported. If Codex model overrides are added later, map the same tiers to
  Codex-native model names.
- Shared behavior, routing, and workflow instructions belong in
  `core/prompts/`.
