# Pathly Agent Skills

This directory exposes Pathly's Codex-safe skill wrappers for direct agent skill
discovery.

`skills/` intentionally mirrors `adapters/codex/skills/` as plain files instead
of symlinks. This keeps the repository portable across Windows, GitHub, local
marketplaces, and tools that copy skill folders rather than preserving links.

Do not edit files under `.agents/skills/` directly. Update
`adapters/codex/skills/` first, then refresh the mirror and run the packaging
tests.
