# pathly-adapters

Stitches Pathly agent files and installs them into AI host tools (Claude Code, Codex, Copilot).

## Install

```bash
pip install -e pathly-adapters/
```

## Usage

```bash
pathly-setup                        # detect hosts; no writes
pathly-setup --dry-run              # preview what would be written, validate YAMLs
pathly-setup --apply                # install into all detected hosts
pathly-setup claude --apply         # install for Claude Code only
pathly-setup codex --apply          # install for Codex only
pathly-setup copilot --apply        # install for Copilot / VS Code only
pathly-setup --repair               # overwrite Pathly-owned files
pathly-setup --force                # overwrite all files, even non-Pathly-owned
```

`--dry-run` never writes. `--apply` is required for any writes.

## Supported Hosts

| Host | Detected by | Default destination |
|------|-------------|---------------------|
| `claude` | `~/.claude/` directory exists | `~/.claude/agents/` |
| `codex` | Codex config directory exists | Codex agents folder |
| `copilot` | VS Code + Copilot detected | VS Code agents folder |

## How It Works

1. **Detect** — scans for installed hosts on the current machine.
2. **Stitch** — combines `core/agents/<name>.md` with adapter-specific `_meta/<name>.yaml` to produce the final agent file (frontmatter + body + spawn section).
3. **Materialize** — writes stitched files to the host config location. A manifest tracks Pathly-owned files; `--repair` overwrites owned files, `--force` overwrites everything.

## Release Status

Public beta. Core install path (`--dry-run`, `--apply`) is verified. Copilot destination paths depend on the VS Code Copilot agent spec, which may change.
