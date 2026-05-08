# Multi-Tool Architecture Design

Pathly is no longer a Claude-only file layout. The current repository already
uses a core-plus-adapters structure so the same workflow contracts can be
packaged for Claude Code, Codex, the Python CLI, and future hosts.

## Current Structure

```text
pathly/
|-- core/                     # host-neutral prompts, agent contracts, templates
|   |-- agents/               # pure role contracts
|   |-- prompts/              # workflow instructions
|   `-- templates/plan/       # canonical plan file templates
|-- adapters/
|   |-- claude-code/          # Claude plugin, slash-command skills, agent wrappers
|   |-- codex/                # Codex plugin skills and manifest
|   `-- cli/                  # terminal command contract docs
|-- .agents/                  # Codex marketplace metadata and direct skill mirror
|-- pathly/                   # Python package and CLI implementation
|-- orchestrator/             # filesystem FSM runtime package
|-- docs/                     # architecture, readiness, and review notes
|-- tests/                    # packaging, CLI, hook, runner, and FSM tests
`-- README.md
```

## Source Of Truth

- Shared workflow behavior belongs in `core/prompts/`.
- Shared role behavior belongs in `core/agents/`.
- Plan file structure belongs in `core/templates/plan/`.
- Host metadata belongs under the matching adapter.
- Python runtime code belongs in `pathly/` or `orchestrator/`, not in `core/`.

Adapters should stay thin. They load or wrap core content, add host-specific
metadata, and expose the host-native invocation style.

## Current Adapters

| Adapter | Current surface | Files |
|---|---|---|
| Claude Code | `/pathly ...`, `/path ...`, plus legacy direct commands | `adapters/claude-code/` |
| Codex | Natural-language plugin prompts such as `Use Pathly help` | `adapters/codex/` |
| Direct agent skills | Tools that scan `.agents/skills/<name>/SKILL.md` | `.agents/skills/` |
| CLI | `pathly ...` terminal commands | `pathly/cli/` and `adapters/cli/README.md` |

`.agents/skills/` mirrors `adapters/codex/skills/` as files rather than
symlinks. Update the Codex adapter first, then refresh the mirror.

## Installed Manifests

- Claude plugin manifest: `adapters/claude-code/.claude-plugin/plugin.json`
- Claude marketplace metadata: `adapters/claude-code/.claude-plugin/marketplace.json`
- Codex plugin manifest: `adapters/codex/.codex-plugin/plugin.json`
- Public Codex marketplace metadata: `.agents/plugins/marketplace.json`

There is no root `.codex-plugin/` directory in the current repository. Root
`.agents/` is marketplace and direct-skill compatibility metadata.

## Future Adapter Work

Cursor, Windsurf, BMAD chat modes, and generic copy-paste prompt packs remain
planned work. Add them only when there is real demand, and keep the same rule:
core owns reusable behavior, adapters own packaging.

Suggested future layout:

```text
adapters/
|-- cursor/
|-- windsurf/
|-- bmad/
`-- generic/
```

## Release Guidance

Do not describe future adapters as shipped. Current public positioning should
remain: Pathly is a public beta candidate with Claude Code, Codex, direct skill,
and CLI surfaces available, while additional adapters are roadmap items.
