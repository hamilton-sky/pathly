# clean-filesystem - Progress

## Status: BUILDING

## Story Status

| Story | Title | Delivered by | Status |
|-------|-------|--------------|--------|
| S1.1 | Runtime entrypoints are canonical | Conv 1 | DONE |
| S1.2 | Runtime code is packaged predictably | Conv 4 | TODO |
| S2.1 | Agent execution uses a host-neutral runner | Conv 2 | TODO |
| S3.1 | Hooks are portable runtime modules | Conv 3 | TODO |
| S4.1 | Legacy files are removed only after replacements pass | Conv 4 | TODO |

## Conversation Breakdown

| Conv | Phases | Stories | Depends On | Status | Verify |
|------|--------|---------|------------|--------|--------|
| 1 | Phase 1 | S1.1 | Baseline `pytest -q` green | DONE | `python -m pathly.cli --help`; `python -m pathly.team_flow --help`; `pathly --help`; `pytest -q` |
| 2 | Phase 2 | S2.1 | Conv 1 DONE | TODO | `pytest -q`; optional `codex exec -C . "Use Pathly help"` |
| 3 | Phase 3 | S3.1 | Conv 1 DONE; Conv 2 not blocked | TODO | `pathly hooks print-config claude`; `pathly hooks run post-tool-use --payload <fixture-json>`; `pytest -q` |
| 4 | Phases 4-5 | S4.1, S1.2 | Convs 1-3 DONE | TODO | cleanup search; `pytest -q`; `python -m build` |

See **CONVERSATION_PROMPTS.md** for exact implementation prompts.

## Phase Detail

| # | Phase | Layer | Description | Conv | Status | Key Files |
|---|-------|-------|-------------|------|--------|-----------|
| 1 | Stabilize package entrypoints | CLI/runtime | Make canonical package entrypoints work before cleanup. | 1 | DONE | `pathly/cli/`, `pathly/team_flow/`, `pyproject.toml`, `tests/` |
| 2 | Introduce runner interface | Runtime orchestration | Add shared runner contract and Claude/Codex runner selection. | 2 | TODO | `pathly/runners/`, runtime manager/driver files, `tests/` |
| 3 | Modularize hooks | Runtime hooks | Move hook behavior into `pathly/hooks/` and add hook CLI surfaces. | 3 | TODO | `pathly/hooks/`, CLI command files, `tests/` |
| 4 | Remove legacy files and generated drift | Repo hygiene | Delete only verified legacy files and resolve `.agents/skills/` drift. | 4 | TODO | legacy bridge files, `scripts/`, root `hooks/`, `.agents/skills/` |
| 5 | Packaging gate | Packaging | Build and inspect install artifacts after cleanup. | 4 | TODO | `pyproject.toml`, packaging tests, install docs if needed |

## Prerequisites

- Baseline `pytest -q` is green before Conversation 1 starts.
- Unrelated working-tree changes are separated from cleanup work before deletion.

## Blocked By

- Nothing.
