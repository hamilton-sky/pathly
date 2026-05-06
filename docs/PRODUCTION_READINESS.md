# Pathly Production Readiness

This checklist tracks what must be true before Pathly should be treated as a
polished public release rather than a working local framework.

## Release Position

Pathly is currently best described as:

- Supported for Claude Code through the existing install scripts.
- Ready for Codex local-plugin testing through `.codex-plugin/plugin.json`.
- Not yet a standalone Python CLI.
- Not yet fully adapter-based for Cursor, Windsurf, BMAD, or generic prompts.

## User Install

Required before public release:

- Keep the Claude Code install scripts working on macOS, Linux, and Windows.
- Validate `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` as JSON.
- Document exactly what each install path writes and how to uninstall it.
- Add a smoke test that confirms every documented skill exists under
  `adapters/claude-code/skills/`.
- Add a smoke test that confirms every README command maps to a real skill.

Recommended next:

- Add a `pathly` CLI only when it does real setup work:
  - `pathly install claude`
  - `pathly install codex`
  - `pathly doctor`
  - `pathly uninstall`
- Publish Python packaging only as a developer/contributor install until the CLI
  exists.

## Naming

Public brand:

- `Pathly`

Current internal package:

- `pathly`

The Python distribution has been renamed to `pathly`. The local checkout folder
or GitHub repository may still have an older name until the remote repository is
renamed.

Before publishing broadly:

- Check GitHub repository name availability.
- Check PyPI package name availability.
- Check npm package name availability if a Node-based CLI is planned.
- Keep uninstall cleanup scoped to the current installed Claude plugin directory
  `pathly`.

## Codex Readiness

Done:

- Add `.codex-plugin/plugin.json`.
- Point Codex at `./adapters/codex/skills/`.
- Position Claude-style agents as role contracts for now.

Still needed:

- Test local plugin install in Codex.
- Confirm how Codex should discover or display the skill commands.
- Decide whether `adapters/claude-code/agents/` needs a Codex-native equivalent
  or can remain reference material.
- Add Codex-specific install screenshots or exact UI steps once verified.

## Multi-Tool Adapters

Use [MULTI_TOOL_DESIGN.md](MULTI_TOOL_DESIGN.md) as the long-term architecture,
but do not block the next release on it.

Adapter work should begin when there is real demand for:

- Cursor rules.
- Windsurf rules.
- BMAD chat modes.
- Generic copy-paste prompts.

## Quality Gates

Required:

- `pytest -q` passes.
- Plugin manifests parse as JSON.
- Install scripts pass a dry-run or temp-home smoke test.
- README start commands are covered by skill existence checks.
- Security and reliability notes are current.

Recommended:

- Changelog for every public release.
- Version tag before large restructuring.
- Known limitations section in README.
- Example walkthroughs:
  - New feature through `/go`.
  - Bug fix through `/debug`.
  - Stuck state through `/help --doctor`.
  - Codebase question through `/explore`.

## Security Notes

Before broad distribution, make these explicit in README:

- Install scripts write to user-level AI tool config directories.
- Hook setup modifies Claude Code settings only when the user runs the hook
  setup script.
- Hooks run local Python scripts from the installed plugin directory.
- No production source files are modified by install scripts.
- No network access is required after the repository is cloned.
