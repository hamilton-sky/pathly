# installable-workflow-architecture - Conversation Guide

Split into 4 conversations. Each conversation should leave the codebase
runnable and testable. After each conversation, commit your changes before
starting the next.

---

## Conversation 1: Installability Foundation (Phases 1-2)

**Stories delivered:** S1.1, S1.2

**Prompt to paste:**
```text
Implement installable-workflow-architecture Conversation 1 (Phases 1-2) from plans/installable-workflow-architecture/IMPLEMENTATION_PLAN.md.

Scope:
- Phase 1: Add a host-neutral package resource contract for core prompts, role contracts, templates, and adapter assets. Prefer `importlib.resources` behavior and avoid repo-root assumptions for packaged assets.
- Phase 2: Add clean install smoke coverage and a `pathly --version` path. Prove the installed CLI can run from a non-Pathly project directory.

Architectural boundaries:
- Keep `core/` and `adapters/` as packaged assets, not runtime behavior owners.
- Keep `pathly/` as the installable Python package and `orchestrator/` as the FSM runtime package.
- Do not add `pathly setup` yet except for placeholders required by tests. Setup mutation belongs to Conversation 2.
- Do not change hook behavior yet.

Expected file areas:
- `pathly/resources.py`
- `pathly/cli/manager.py`
- `pathly/__init__.py`
- `pyproject.toml`
- `tests/test_project_packaging.py`
- `tests/test_cli.py`

Do NOT touch setup materialization, hook install semantics, or host docs yet.

Verify:
- `python -m build`
- installed-wheel smoke for `pathly --version`, `pathly --help`, `pathly doctor`, and `pathly help` from a temporary non-Pathly directory
- `pytest tests/test_cli.py tests/test_project_packaging.py -q`

After done, update plans/installable-workflow-architecture/PROGRESS.md phases 1-2 and stories S1.1-S1.2 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report. If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** Installed-package resource loading is test-covered, `pathly --version` works, and clean install smoke is either automated or documented with a focused test.
**Files touched:** `pathly/resources.py`, CLI/package metadata files, packaging and CLI tests.

---

## Conversation 2: Setup Without Surprise (Phases 3-4)

**Stories delivered:** S2.1, S2.2

**Prompt to paste:**
```text
Implement installable-workflow-architecture Conversation 2 (Phases 3-4) from plans/installable-workflow-architecture/IMPLEMENTATION_PLAN.md.

Scope:
- Phase 3: Add `pathly setup` diagnostics and dry-run behavior. Default setup to a safe report unless `--apply` is present.
- Phase 4: Add adapter materialization from packaged resources into approved versioned user data snapshots, with `--repair` and `--force` semantics.

Architectural boundaries:
- Setup detects hosts, prints planned writes, and materializes adapter files only when explicitly applying.
- Setup must not advance workflow state, spawn lifecycle agents, or interpret FSM transitions.
- Adapters remain thin host wrappers over `core/` assets.
- Codex docs and output must keep natural-language invocation, not `/pathly`.

Expected file areas:
- `pathly/cli/setup_command.py`
- `pathly/setup/locations.py`
- `pathly/setup/detect.py`
- `pathly/setup/plan.py`
- `pathly/setup/materialize.py`
- `pathly/cli/manager.py`
- `pathly/cli/installers/codex.py`
- `tests/test_setup.py`
- adapter README files only if command behavior changes

Do NOT touch status/doctor recovery UX, hook hardening, or broad README release claims yet.

Verify:
- `pytest tests/test_setup.py tests/test_cli.py -q`
- `pathly setup --dry-run`
- `pathly setup claude --dry-run`
- `pathly setup codex --dry-run`

After done, update plans/installable-workflow-architecture/PROGRESS.md phases 3-4 and stories S2.1-S2.2 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report. If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** Setup can report safely without writes and can apply adapter files from packaged resources with clear conflict handling.
**Files touched:** setup command/module files, Codex installer refactor, setup tests, narrow adapter docs if needed.

---

## Conversation 3: Recovery And Hooks (Phases 5-6)

**Stories delivered:** S3.1, S3.2

**Prompt to paste:**
```text
Implement installable-workflow-architecture Conversation 3 (Phases 5-6) from plans/installable-workflow-architecture/IMPLEMENTATION_PLAN.md.

Scope:
- Phase 5: Add `pathly status [feature]` and improve `pathly doctor` so install, adapter, hook, and workflow-state problems are distinct.
- Phase 6: Harden hook path validation and diagnostics while keeping hooks bounded guardrails.

Architectural boundaries:
- Status and doctor may read filesystem state and summarize next actions, but they must not advance lifecycle state.
- Orchestrator/event log remains the source of lifecycle truth.
- Hooks may validate, classify, annotate, and report. They must not spawn lifecycle agents, edit source code, or advance FSM state.
- Keep `meet` read-only and do not add director as a consult target.

Expected file areas:
- `pathly/cli/status_command.py`
- `pathly/cli/manager.py`
- `pathly/cli/help_command.py`
- `pathly/cli/plans.py`
- `pathly/hooks/contracts.py`
- `pathly/hooks/inject_feedback_ttl.py`
- `pathly/hooks/classify_feedback.py`
- `pathly/cli/hooks_command.py`
- `tests/test_cli.py` or `tests/test_status.py`
- `tests/test_hooks.py`

Do NOT touch setup adapter materialization except for small integration fixes needed by doctor/status. Do NOT make hooks a workflow driver.

Verify:
- `pytest tests/test_cli.py tests/test_hooks.py -q`
- `pathly status`
- `pathly doctor`
- `pathly hooks run post-tool-use --payload <fixture-json>`

After done, update plans/installable-workflow-architecture/PROGRESS.md phases 5-6 and stories S3.1-S3.2 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report. If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** Users can understand recovery state from CLI output, and hooks have stronger validation without becoming hidden automation.
**Files touched:** status/doctor CLI files, hook runtime files, CLI/status/hook tests.

---

## Conversation 4: Host Smoke And Documentation (Phase 7)

**Stories delivered:** S4.1

**Prompt to paste:**
```text
Implement installable-workflow-architecture Conversation 4 (Phase 7) from plans/installable-workflow-architecture/IMPLEMENTATION_PLAN.md.

Scope:
- Phase 7: Align README, production readiness docs, proposal/recommendation docs, adapter docs, and setup output with verified behavior.
- Add or update static tests that keep public commands and docs aligned.
- Run the host smoke matrix where local hosts are available and record any skipped host smoke honestly.

Architectural boundaries:
- Public-facing release language must remain honest: public beta candidate, not production-ready.
- Docs must not claim host behavior that was not verified.
- Claude Code slash-command examples and Codex natural-language examples must stay separate.
- Do not add new workflow features in this docs/smoke conversation unless required to fix drift found by verification.

Expected file areas:
- `README.md`
- `docs/PRODUCTION_READINESS.md`
- `docs/INSTALLABLE_WORKFLOW_ARCHITECTURE_PROPOSAL.md`
- `docs/INSTALLABLE_WORKFLOW_ARCHITECTURE_RECOMMENDATIONS.md`
- `adapters/claude-code/README.md`
- `adapters/codex/README.md`
- `adapters/cli/README.md`
- `tests/test_project_packaging.py`

Do NOT touch resource/setup/status/hook implementation except for small docs-test alignment fixes.

Verify:
- `pytest -q`
- `pathly go "add password reset"`
- Claude Code smoke if available: `/pathly help`; `/pathly add password reset`
- Codex smoke if available: `Use Pathly help`; `Use Pathly to add password reset`
- Optional hook smoke if hooks are installed

After done, update plans/installable-workflow-architecture/PROGRESS.md phase 7 and story S4.1 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report. If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** Docs, setup output, and smoke evidence match the actual implemented behavior.
**Files touched:** README/docs/adapter docs and static docs tests.
