# pathly-two-project-split — Implementation Plan

## Overview

Split Pathly into two independent, installable Python projects. No shared
imports. Communication between projects happens only through the filesystem
(`plans/`, `STATE.json`, `EVENTS.jsonl`).

## Confirmed Architecture

```
pathly-adapters/             ← pip install pathly-adapters
  core/
    agents/                  ← Claude/Codex/Copilot read these at runtime
    skills/
    templates/
  adapters/
    claude/                  ← plugin files + YAML install config
    codex/                   ← plugin files + YAML install config
    copilot/                 ← plugin files + YAML install config
  install_cli/               ← pathly-setup: copies files into host, that's all
    __init__.py
    __main__.py
    detect.py                detects which hosts are installed
    resources.py             reads assets from core/ and adapters/
    materialize.py           copies assets into host config locations
    stitch.py                combines core/agents/ + adapter _meta YAML → final file
    setup_command.py         CLI: pathly-setup [host] [--dry-run] [--apply]
  pyproject.toml

pathly-engine/               ← pip install pathly-engine  (optional)
  orchestrator/
    state.py
    events.py
    eventlog.py
    reducer.py
    feedback.py
    agent_runner.py
  runners/
  team_flow/
  engine_cli/                ← pathly go / status / doctor from plain terminal
    __init__.py
    __main__.py
    manager.py
  pyproject.toml
```

## Key Rules

- **No imports across projects.** pathly-adapters never imports pathly-engine.
- **AI tool IS the FSM runner.** When user runs `/pathly go` in Claude Code,
  Claude reads installed agent files and follows the workflow. No Python process
  spawned. State lives in the filesystem.
- **pathly-adapters is a one-time installer.** Run once, files copied, done.
- **pathly-engine is optional.** Only needed for external/programmatic control.
- **Install options:**
  ```
  pip install pathly-adapters             ← file installer only
  pip install pathly-adapters[engine]     ← also installs pathly-engine
  pip install pathly-engine               ← engine only, no installer
  ```

## What is already done (from merged plans)

- No-argument verbs: `/pathly start`, `continue`, `end`, `meet`, `help`
- Agent meta YAML files for all adapters (claude, codex, copilot)
- Package resource contract (`resources.py`)
- Clean install smoke (`pathly --version`, `pathly --help`)

## Phases

### Phase 1: Two-project repo restructure
**Conv:** 1
**Purpose:** Create the two project folders with correct structure, pyproject.toml,
and no cross-imports. Existing code moves; no new behavior yet.
**Files:**
- `pathly-adapters/pyproject.toml`
- `pathly-adapters/core/` ← moved from `core/`
- `pathly-adapters/adapters/` ← moved from `adapters/`
- `pathly-adapters/install_cli/__init__.py` (skeleton)
- `pathly-engine/pyproject.toml`
- `pathly-engine/orchestrator/` ← moved from `orchestrator/`
- `pathly-engine/runners/` ← moved from `pathly/runners/`
- `pathly-engine/team_flow/` ← moved from `pathly/team_flow/`
- `pathly-engine/engine_cli/__init__.py` (skeleton)
- `tests/test_project_structure.py`

**Verify:**
- `pip install -e pathly-adapters/`
- `pip install -e pathly-engine/`
- `pytest tests/test_project_structure.py -q` (confirms no cross-imports)

### Phase 2: Install CLI and stitcher
**Conv:** 2
**Purpose:** `pathly-setup` detects hosts, stitches core agents + meta YAML into
final files, and copies them into host config locations.
**Files:**
- `pathly-adapters/install_cli/detect.py`
- `pathly-adapters/install_cli/resources.py`
- `pathly-adapters/install_cli/materialize.py`
- `pathly-adapters/install_cli/stitch.py`
- `pathly-adapters/install_cli/setup_command.py`
- `pathly-adapters/adapters/claude/_meta/install.yaml`
- `pathly-adapters/adapters/codex/_meta/install.yaml`
- `pathly-adapters/adapters/copilot/_meta/install.yaml`
- `tests/test_setup.py`
- `tests/test_stitch.py`

**Verify:**
- `pathly-setup --dry-run`
- `pathly-setup claude --dry-run`
- `pathly-setup codex --dry-run`
- `pytest tests/test_setup.py tests/test_stitch.py -q`

### Phase 3: Engine CLI
**Conv:** 3
**Purpose:** `pathly go`, `pathly status`, `pathly doctor` work from a plain
terminal without any AI tool open.
**Files:**
- `pathly-engine/engine_cli/manager.py`
- `pathly-engine/engine_cli/__main__.py`
- `pathly-engine/pyproject.toml` (scripts entry point)
- `tests/test_engine_cli.py`

**Verify:**
- `pathly go "add password reset"` (from terminal, no AI tool)
- `pathly status`
- `pathly doctor`
- `pytest tests/test_engine_cli.py -q`

### Phase 4: Docs alignment
**Conv:** 4
**Purpose:** README and adapter docs match verified behavior. Public beta
language only — no claims about unverified host behavior.
**Files:**
- `README.md`
- `pathly-adapters/README.md`
- `pathly-engine/README.md`
- `pathly-adapters/adapters/claude/README.md`
- `pathly-adapters/adapters/codex/README.md`
- `pathly-adapters/adapters/copilot/README.md`
- `tests/test_project_packaging.py`

**Verify:**
- `pytest -q`
- Manual host smoke where available
