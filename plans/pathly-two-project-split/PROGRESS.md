# pathly-two-project-split — Progress

## Status: COMPLETE

## Story Status

| Story | Title | Delivered by | Status |
|-------|-------|--------------|--------|
| S1.1 | Repo splits into two independent installable projects | Conv 1 | DONE |
| S2.1 | pathly-setup detects hosts and reports planned writes | Conv 2 | DONE |
| S2.2 | pathly-setup stitches and installs adapter files into hosts | Conv 2 | DONE |
| S3.1 | pathly go / status / doctor work from terminal without AI tool | Conv 3 | DONE |
| S4.1 | README and adapter docs match verified behavior | Conv 4 | DONE |

## Conversation Breakdown

| Conv | Phases | Stories | Depends On | Status | Verify |
|------|--------|---------|------------|--------|--------|
| 1 | Phase 1 | S1.1 | Baseline tests known | DONE | `pip install -e pathly-adapters/`; `pip install -e pathly-engine/`; `pytest tests/test_project_structure.py -q` |
| 2 | Phase 2 | S2.1, S2.2 | Conv 1 DONE | DONE | `pathly-setup --dry-run`; `pytest tests/test_setup.py tests/test_stitch.py -q` |
| 3 | Phase 3 | S3.1 | Conv 1 DONE | DONE | `pathly go "add password reset"`; `pytest tests/test_engine_cli.py -q` |
| 4 | Phase 4 | S4.1 | Convs 1-3 DONE | DONE | `pytest -q`; host smoke where available |

See **CONVERSATION_PROMPTS.md** for exact prompts to paste in each conversation.

## Phase Detail

| # | Phase | Layer | Description | Conv | Status | Key Files |
|---|-------|-------|-------------|------|--------|-----------|
| 1 | Two-project repo restructure | both | Create pathly-adapters/ and pathly-engine/ as separate installable projects. Move files. No new behavior. | 1 | DONE | `pathly-adapters/pyproject.toml`, `pathly-engine/pyproject.toml`, `tests/test_project_structure.py` |
| 2 | Install CLI and stitcher | pathly-adapters | detect.py + resources.py + materialize.py + stitch.py + setup_command.py. Stitches core agents + meta YAML → final files and copies to host. | 2 | DONE | `pathly-adapters/install_cli/`, `tests/test_setup.py`, `tests/test_stitch.py` |
| 3 | Engine CLI | pathly-engine | pathly go / status / doctor from plain terminal without AI tool. | 3 | DONE | `pathly-engine/engine_cli/manager.py`, `tests/test_engine_cli.py` |
| 4 | Docs alignment | both | README and adapter docs match verified behavior. Public beta language only. | 4 | DONE | `README.md`, `pathly-adapters/README.md`, `pathly-engine/README.md`, adapter READMEs |

## Already Done (carried over from merged plans)

| Item | Source plan |
|------|-------------|
| No-argument verbs: `/pathly start`, `continue`, `end`, `meet`, `help` | pathly-interface-redesign Conv 1 |
| Agent meta YAML files for all adapters (claude, codex, copilot) | pathly-interface-redesign Conv 2 |
| Package resource contract (`resources.py`) | installable-workflow-architecture Conv 1 |
| Clean install smoke (`pathly --version`, `pathly --help`) | installable-workflow-architecture Conv 1 |

## Blocked By

Nothing.
