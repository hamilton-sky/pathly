# installable-workflow-architecture - Progress

## Status: NOT STARTED

## Story Status

| Story | Title | Delivered by | Status |
|-------|-------|--------------|--------|
| S1.1 | Package assets load from an installed package | Conv 1 | TODO |
| S1.2 | Clean install smoke works outside the source checkout | Conv 1 | TODO |
| S2.1 | Setup reports before it mutates | Conv 2 | TODO |
| S2.2 | Setup materializes adapters safely | Conv 2 | TODO |
| S3.1 | Status and doctor explain recovery | Conv 3 | TODO |
| S3.2 | Hooks stay bounded guardrails | Conv 3 | TODO |
| S4.1 | Host smoke and docs match verified behavior | Conv 4 | TODO |

## Conversation Breakdown

| Conv | Phases | Stories | Depends On | Status | Verify |
|------|--------|---------|------------|--------|--------|
| 1 | Phases 1-2 | S1.1, S1.2 | Baseline tests known | TODO | `python -m build`; installed-wheel smoke; `pytest tests/test_cli.py tests/test_project_packaging.py -q` |
| 2 | Phases 3-4 | S2.1, S2.2 | Conv 1 DONE | TODO | `pytest tests/test_setup.py tests/test_cli.py -q`; `pathly setup --dry-run` |
| 3 | Phases 5-6 | S3.1, S3.2 | Conv 2 DONE | TODO | `pytest tests/test_cli.py tests/test_hooks.py -q`; `pathly status`; `pathly doctor` |
| 4 | Phase 7 | S4.1 | Convs 1-3 DONE | TODO | `pytest -q`; host smoke matrix where available |

See **CONVERSATION_PROMPTS.md** for exact prompts to paste in each conversation.

## Phase Detail

| # | Phase | Layer | Description | Conv | Status | Key Files |
|---|-------|-------|-------------|------|--------|-----------|
| 1 | Package resource contract | Packaging/runtime resources | Add one host-neutral resource API for packaged prompts, templates, agents, and adapters. | 1 | TODO | `pathly/resources.py`, `pyproject.toml`, `tests/test_project_packaging.py` |
| 2 | Clean install smoke and version command | Packaging/CLI | Prove installed Pathly works from a fresh environment and non-Pathly project. | 1 | TODO | `pathly/cli/manager.py`, `pathly/__init__.py`, packaging and CLI tests |
| 3 | Setup diagnostics and dry run | CLI/setup | Add transparent setup reporting before mutation. | 2 | TODO | `pathly/cli/setup_command.py`, `pathly/setup/`, `tests/test_setup.py` |
| 4 | Adapter materialization | Setup/adapters | Copy versioned adapter snapshots from packaged resources into user data locations. | 2 | TODO | `pathly/setup/materialize.py`, `pathly/cli/installers/codex.py`, adapter docs |
| 5 | Status and doctor UX | CLI/workflow status | Show install, adapter, hook, and workflow recovery state with suggested next actions. | 3 | TODO | `pathly/cli/status_command.py`, `pathly/cli/plans.py`, CLI tests |
| 6 | Hook hardening | Runtime hooks | Canonicalize hook paths, improve diagnostics, and preserve hook boundaries. | 3 | TODO | `pathly/hooks/`, `pathly/cli/hooks_command.py`, `tests/test_hooks.py` |
| 7 | Host smoke and docs alignment | Docs/host surfaces | Align README/docs/setup output with verified CLI, Claude Code, Codex, and hook behavior. | 4 | TODO | `README.md`, `docs/`, `adapters/*/README.md`, packaging tests |

## Prerequisites

- Baseline test status is known before Conversation 1 starts.
- Build tooling is available for `python -m build`.
- Claude Code and Codex manual smoke can be skipped only when those hosts are not
  available, with the gap recorded in docs.

## Blocked By

- Nothing.
