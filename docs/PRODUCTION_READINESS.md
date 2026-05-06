# Pathly Production Readiness

This checklist tracks what must be true before Pathly should be treated as a
production-ready release. Until those gates are met, describe Pathly publicly as
a public beta / technical preview.

## Release Position

Pathly is currently best described as:

- Public beta candidate for Claude Code and Codex workflows.
- Supported for Claude Code through the existing install scripts.
- Ready for Codex plugin testing through `.codex-plugin/plugin.json` and the
  local marketplace helper.
- Packaged as a Python CLI named `pathly` for install guidance, project plan
  initialization, status menus, doctor checks, and the Python team-flow driver.
- Not yet production-ready: end-to-end agent runs, hook hardening, public case
  studies, and release/versioning policy still need to be finished.
- Not yet fully adapter-based for Cursor, Windsurf, BMAD, or generic prompts.

## User Install

Required before calling the release production-ready:

- Keep the Claude Code install scripts working on macOS, Linux, and Windows.
- Validate `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and
  adapter manifests as JSON.
- Document exactly what each install path writes and how to uninstall it.
- Keep smoke tests that confirm every documented skill exists under
  `adapters/claude-code/skills/`.
- Keep smoke tests that confirm every README command maps to a real skill.
- Add a clean-machine smoke run for Claude Code install and uninstall.
- Add a clean-machine smoke run for Codex local marketplace install.

Current CLI scope:

- `pathly install claude` prints Claude Code setup guidance.
- `pathly install codex` prints Codex local marketplace setup guidance.
- `pathly install codex --apply` creates the Codex local marketplace files.
- `pathly init <feature>` creates a lite starter plan.
- `pathly help`, `pathly doctor`, `pathly debug`, `pathly explore`, and
  `pathly review` expose stable local fallback surfaces.
- `pathly flow <feature>` runs the Python team-flow driver when the required
  host tooling is available.

Recommended next:

- Add `pathly uninstall` only when it can clean up each supported adapter safely.
- Add a manual smoke-test guide that records one successful run through each
  major front door: `go`, `debug`, `explore`, `review`, and `doctor`.
- Publish Python packaging as beta until the clean-machine smoke matrix is done.

## Naming

Public brand:

- `Pathly`

Current internal package:

- `pathly`

The Python distribution has been renamed to `pathly`. The local checkout folder
and GitHub repository should use the same name before a broad announcement.

Before publishing broadly:

- Check GitHub repository name availability and public repository settings.
- Check PyPI package name availability.
- Check npm package name availability if a Node-based CLI is planned.
- Keep uninstall cleanup scoped to the current installed Claude plugin directory
  `pathly`.

## Codex Readiness

Done:

- Add `.codex-plugin/plugin.json`.
- Point Codex at `./adapters/codex/skills/`.
- Add `.agents/skills/` as a direct skill-discovery mirror for Codex-safe
  wrappers.
- Add `pathly install codex --apply` to create a local marketplace.
- Position Claude-style agents as role contracts for now.

Still needed:

- Test local plugin install in a clean Codex environment.
- Confirm how Codex displays the skill prompts in the current app build.
- Decide whether `adapters/claude-code/agents/` needs a Codex-native equivalent
  or can remain reference material.
- Add Codex-specific install screenshots or exact UI steps once verified.

## Multi-Tool Adapters

Use [MULTI_TOOL_DESIGN.md](MULTI_TOOL_DESIGN.md) as the long-term architecture,
but do not block the beta release on it.

Adapter work should begin when there is real demand for:

- Cursor rules.
- Windsurf rules.
- BMAD chat modes.
- Generic copy-paste prompts.

## Quality Gates

Required before production-ready:

- `pytest -q` passes.
- GitHub Actions green on Python 3.11, 3.12, and 3.13.
- Plugin manifests parse as JSON.
- Install scripts pass dry-run or temp-home smoke tests.
- README start commands are covered by skill existence checks.
- Security and reliability notes are current.
- Public known-limitations section exists in README.
- At least three public walkthroughs or case studies exist:
  - Tiny change through `nano`.
  - Bug fix through `debug`.
  - Feature through `lite` or `standard`.

Recommended:

- Changelog for every public release.
- Version tag before large restructuring.
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
- Plans, PRDs, rules, and generated prompts are trusted workflow inputs; see
  [SECURITY_RELIABILITY_REVIEW.md](SECURITY_RELIABILITY_REVIEW.md) for the trust
  boundary model and remaining hardening work.