# Pathly Agent Definitions

This directory exposes Pathly's Codex agent definitions for direct agent discovery.

`agents/` intentionally mirrors `adapters/codex/agents/` as plain files instead
of symlinks. This keeps the repository portable across Windows, GitHub, local
marketplaces, and tools that copy agent folders rather than preserving links.

Do not edit files under `.agents/agents/` directly. Update
`adapters/codex/agents/` first, then refresh the mirror.

Skills are loaded directly from `core/skills/` — no mirror or adapter wrapper needed.
