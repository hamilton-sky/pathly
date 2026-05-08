# installable-workflow-architecture - Edge Cases

## Category 1: Package Resource Failures

### EC-1.1: Asset missing from installed wheel
- **Trigger:** A prompt, template, agent contract, or adapter file is omitted
  from the built artifact.
- **Current behavior:** Installer code may fall back to repo-relative paths or
  fail unclearly.
- **Expected behavior:** Resource API raises a clear missing-asset error and
  packaging tests fail before release.
- **Handled in:** Phase 1 / Conv 1

### EC-1.2: Command runs outside a source checkout
- **Trigger:** User runs installed `pathly` from a project that is not this repo.
- **Current behavior:** Commands that rely on `Path(__file__).parents[2]` can
  report wrong paths or missing manifests.
- **Expected behavior:** CLI uses package resources and active project context.
- **Handled in:** Phase 2 / Conv 1

## Category 2: Setup Safety

### EC-2.1: Dry run writes files
- **Trigger:** A setup dry run accidentally calls materialization code.
- **Current behavior:** No `setup` command exists yet.
- **Expected behavior:** Dry run constructs and prints an action plan only.
- **Handled in:** Phase 3 / Conv 2

### EC-2.2: Existing unrelated files in target location
- **Trigger:** User data or host config location contains non-Pathly files.
- **Current behavior:** Existing Codex installer rejects non-empty paths, but the
  policy is not generalized.
- **Expected behavior:** Setup refuses overwrite unless the file is Pathly-owned
  and repairable or the user passes `--force`.
- **Handled in:** Phase 4 / Conv 2

### EC-2.3: Stale Pathly-owned adapter snapshot
- **Trigger:** User upgrades Pathly and old adapter files remain registered.
- **Current behavior:** Repair behavior is not formalized.
- **Expected behavior:** `--repair` refreshes Pathly-owned assets from packaged
  resources and reports what changed.
- **Handled in:** Phase 4 / Conv 2

## Category 3: Workflow Recovery

### EC-3.1: `STATE.json` missing but plan files exist
- **Trigger:** User has plan files but no runtime state file.
- **Current behavior:** Help infers some state from plan files, while doctor is
  limited.
- **Expected behavior:** `pathly status` reports inferred state and suggests a
  real next command.
- **Handled in:** Phase 5 / Conv 3

### EC-3.2: Feedback files disagree with state
- **Trigger:** Feedback files exist while state says a non-blocked lifecycle
  state.
- **Current behavior:** Startup checks handle some drift in team-flow.
- **Expected behavior:** Status/doctor names the blocking feedback file and the
  owner responsible for resolution.
- **Handled in:** Phase 5 / Conv 3

## Category 4: Hook Boundaries

### EC-4.1: Hook path traversal
- **Trigger:** Hook payload points outside the active project or outside
  `plans/`.
- **Current behavior:** Additional path-validation hardening is still planned.
- **Expected behavior:** Hook rejects the payload and emits a visible diagnostic.
- **Handled in:** Phase 6 / Conv 3

### EC-4.2: Unsupported host hook schema
- **Trigger:** User asks setup to register hooks for a host without a documented
  native hook schema.
- **Current behavior:** Some config output is explicit, but setup orchestration
  does not exist yet.
- **Expected behavior:** Setup reports unavailable hook registration rather than
  pretending it works.
- **Handled in:** Phase 6 / Conv 3

## Known Limitations

- Host smoke depends on Claude Code and Codex availability on the verification
  machine.
- This plan does not add Cursor, Windsurf, BMAD, or generic prompt adapters.
- This plan does not add a dashboard or autonomous multi-worktree orchestration.
