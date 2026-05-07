# clean-filesystem - Edge Cases

## Entrypoint Compatibility

### EC-1.1: Console script works but module execution fails
- **Trigger:** `pathly --help` works through an old bridge while
  `python -m pathly.cli --help` fails.
- **Current behavior:** Installed and local paths may diverge.
- **Expected behavior:** Conversation 1 fixes canonical package entrypoints
  before any deletion.
- **Handled in:** Phase 1 / Conv 1

### EC-1.2: Tests still import `scripts.team_flow`
- **Trigger:** Legacy tests keep the old script package alive.
- **Current behavior:** Cleanup can appear unsafe because imports still point at
  `scripts/`.
- **Expected behavior:** Tests import canonical runtime paths before legacy
  deletion is attempted.
- **Handled in:** Phase 1 / Conv 1

## Runner Behavior

### EC-2.1: Codex CLI has no stable JSON usage output
- **Trigger:** Codex execution returns plain text or an unstable schema.
- **Current behavior:** Usage metadata cannot be parsed reliably.
- **Expected behavior:** Codex runner returns stdout, stderr, and return code
  with empty usage metadata.
- **Handled in:** Phase 2 / Conv 2

### EC-2.2: Runner selection is omitted
- **Trigger:** User invokes team-flow without `--runner`.
- **Current behavior:** Claude behavior is the existing default.
- **Expected behavior:** Runtime uses explicit `--runner` when provided,
  otherwise `PATHLY_RUNNER`, otherwise compatible default behavior.
- **Handled in:** Phase 2 / Conv 2

## Hook Portability

### EC-3.1: Host does not support native hooks
- **Trigger:** Codex or a cloud host has no documented native hook schema.
- **Current behavior:** Root scripts or Claude-specific config cannot be reused
  directly.
- **Expected behavior:** Runtime checkpoints or CLI commands call
  `pathly/hooks/` functions directly.
- **Handled in:** Phase 3 / Conv 3

### EC-3.2: Hook payload is malformed
- **Trigger:** `pathly hooks run` receives invalid JSON or an unsupported event.
- **Current behavior:** Root scripts may fail in host-specific ways.
- **Expected behavior:** CLI reports a clear non-zero failure without modifying
  unrelated files.
- **Handled in:** Phase 3 / Conv 3

## Cleanup Safety

### EC-4.1: Search finds a remaining legacy reference
- **Trigger:** `rg` finds imports or docs pointing at a file scheduled for
  deletion.
- **Current behavior:** Deleting the file can break runtime or docs.
- **Expected behavior:** Deletion is deferred until the reference is migrated or
  explicitly justified.
- **Handled in:** Phase 4 / Conv 4

### EC-4.2: `.agents/skills/` is still needed for compatibility
- **Trigger:** Local Codex adapters or marketplace workflows still expect the
  committed mirror.
- **Current behavior:** Duplicate skill trees can drift.
- **Expected behavior:** Keep it only with an exact-mirror verification, or
  generate it during install/package tests.
- **Handled in:** Phase 4 / Conv 4

## Packaging

### EC-5.1: Wheel omits core prompts or adapters
- **Trigger:** Package discovery includes Python packages but not data assets.
- **Current behavior:** Installed Pathly lacks prompt or skill files.
- **Expected behavior:** Packaging tests inspect artifacts for required
  `core/` and `adapters/` contents.
- **Handled in:** Phase 5 / Conv 4

### EC-5.2: Generated folders leak into artifacts
- **Trigger:** Build includes `.pytest-tmp/`, `.pytest_cache/`, `logs/`, or
  `*.egg-info/`.
- **Current behavior:** Artifacts contain local/generated state.
- **Expected behavior:** Generated folders remain ignored and absent from built
  artifacts.
- **Handled in:** Phase 5 / Conv 4

## Known Limitations

- This plan does not move `orchestrator/` under `pathly/orchestrator/`.
- This plan does not claim native Codex hook registration exists.
- Optional install gates may require local tools such as `pipx`, `python -m build`,
  or Codex CLI to be installed.
