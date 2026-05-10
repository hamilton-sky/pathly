# pathly-two-project-split — Conversation Guide

Split into 4 conversations. Each conversation leaves the codebase runnable
and testable. Commit after each before starting the next.

Architecture reminder:
- pathly-adapters/ — self-contained installer. AI tool IS the FSM runner.
- pathly-engine/ — optional external/programmatic control only.
- No imports cross the boundary between projects.

---

## Conversation 1: Two-project repo restructure

**Stories delivered:** S1.1

**Prompt to paste:**
```text
Implement pathly-two-project-split Conversation 1 from plans/pathly-two-project-split/IMPLEMENTATION_PLAN.md.

Scope — Phase 1: Two-project repo restructure.

Create two independent installable Python projects with no shared imports:

pathly-adapters/
  core/               ← move from core/
    agents/
    skills/
    templates/
  adapters/           ← move from adapters/
    claude/
    codex/
    copilot/
  install_cli/        ← NEW skeleton (empty __init__.py and __main__.py only)
  pyproject.toml      ← NEW: package name pathly-adapters, entry point pathly-setup

pathly-engine/
  orchestrator/       ← move from orchestrator/
  runners/            ← move from pathly/runners/
  team_flow/          ← move from pathly/team_flow/
  engine_cli/         ← NEW skeleton (empty __init__.py and __main__.py only)
  pyproject.toml      ← NEW: package name pathly-engine, entry point pathly

Architectural boundaries:
- pathly-adapters MUST NOT import from pathly-engine.
- pathly-engine MUST NOT import from pathly-adapters.
- Existing tests that still pass after the move should keep passing.
- Do NOT implement any new behavior yet — only restructure and skeleton files.

Expected file areas:
- pathly-adapters/pyproject.toml
- pathly-adapters/core/ (moved)
- pathly-adapters/adapters/ (moved)
- pathly-adapters/install_cli/__init__.py
- pathly-adapters/install_cli/__main__.py
- pathly-engine/pyproject.toml
- pathly-engine/orchestrator/ (moved)
- pathly-engine/runners/ (moved)
- pathly-engine/team_flow/ (moved)
- pathly-engine/engine_cli/__init__.py
- pathly-engine/engine_cli/__main__.py
- tests/test_project_structure.py (NEW: confirms no cross-imports)

Verify:
- pip install -e pathly-adapters/
- pip install -e pathly-engine/
- pytest tests/test_project_structure.py -q

After done, update plans/pathly-two-project-split/PROGRESS.md phase 1 and story S1.1 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
```

**Expected output:** Two installable Python projects. No cross-imports. Existing behavior preserved.
**Files touched:** Project structure, two new pyproject.toml files, moved directories, skeleton install_cli/ and engine_cli/.

---

## Conversation 2: Install CLI and stitcher

**Stories delivered:** S2.1, S2.2

**Prompt to paste:**
```text
Implement pathly-two-project-split Conversation 2 from plans/pathly-two-project-split/IMPLEMENTATION_PLAN.md.

Scope — Phase 2: Install CLI and stitcher (pathly-adapters project only).

Implement pathly-setup: detects hosts, stitches core agents + adapter meta YAML
into final agent files, and copies them into host config locations.

Files to implement inside pathly-adapters/install_cli/:

detect.py
- Detect installed hosts: claude (looks for ~/.claude/), codex, copilot/vscode
- Return list of detected host names
- No writes, pure detection

resources.py
- Read assets from pathly-adapters/core/ and pathly-adapters/adapters/ using importlib.resources
- Return file paths or content — no assumptions about repo checkout location

stitch.py
- stitch_agent(core_path, meta_path) -> str
- Read meta YAML (name, description, model, tools, can_spawn, spawn_section)
- Build frontmatter from meta fields
- Read core agent body
- Append can_spawn section and spawn_section from meta
- Return complete agent file content as string
- Error clearly on missing core file or malformed YAML

materialize.py
- Copy stitched agent files into host config location
- Support --repair (overwrite Pathly-owned files) and --force (overwrite all)
- Track which files are Pathly-owned (write a manifest)
- Default: skip files not owned by Pathly

setup_command.py
- CLI entry point: pathly-setup [host] [--dry-run] [--apply] [--repair] [--force]
- Default (no --apply): safe report only, no writes
- --dry-run: show what would be written, validate all YAMLs, do not write
- --apply: detect hosts, stitch agents, materialize to host config locations
- Accepts optional host argument to target one host: pathly-setup claude --apply

Also add install.yaml to each adapter _meta/:
pathly-adapters/adapters/claude/_meta/install.yaml
pathly-adapters/adapters/codex/_meta/install.yaml
pathly-adapters/adapters/copilot/_meta/install.yaml

install.yaml format:
  host: claude
  destination: ~/.claude/agents/
  files:
    - source: agents/  (from core + stitched)

Architectural boundaries:
- pathly-adapters/install_cli/ must not import from pathly-engine.
- No writes during --dry-run.
- stitch.py has no side effects — pure function.

Expected file areas:
- pathly-adapters/install_cli/detect.py
- pathly-adapters/install_cli/resources.py
- pathly-adapters/install_cli/stitch.py
- pathly-adapters/install_cli/materialize.py
- pathly-adapters/install_cli/setup_command.py
- pathly-adapters/adapters/claude/_meta/install.yaml
- pathly-adapters/adapters/codex/_meta/install.yaml
- pathly-adapters/adapters/copilot/_meta/install.yaml
- tests/test_setup.py
- tests/test_stitch.py

Verify:
- pathly-setup --dry-run
- pathly-setup claude --dry-run
- pathly-setup codex --dry-run
- pytest tests/test_setup.py tests/test_stitch.py -q

After done, update plans/pathly-two-project-split/PROGRESS.md phase 2 and stories S2.1-S2.2 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
```

**Expected output:** pathly-setup works end-to-end in dry-run mode. stitch_agent() tested. Adapter install.yaml files define host destinations.
**Files touched:** install_cli/ modules, adapter install.yaml files, setup and stitch tests.

---

## Conversation 3: Engine CLI

**Stories delivered:** S3.1

**Prompt to paste:**
```text
Implement pathly-two-project-split Conversation 3 from plans/pathly-two-project-split/IMPLEMENTATION_PLAN.md.

Scope — Phase 3: Engine CLI (pathly-engine project only).

Implement pathly go / pathly status / pathly doctor so they work from a plain
terminal without any AI tool open.

pathly-engine/engine_cli/manager.py:
- pathly go "<intent>"  → reads STATE.json, emits a REQUESTED event, prints next step
- pathly status [feature] → reads STATE.json and EVENTS.jsonl, prints current state and suggested next action
- pathly doctor → checks: engine installed, STATE.json readable, EVENTS.jsonl readable, plans/ accessible; prints per-check pass/fail

pathly-engine/engine_cli/__main__.py:
- Entry point wired to manager

pathly-engine/pyproject.toml:
- scripts entry: pathly = pathly_engine.engine_cli.__main__:main

This is external/programmatic control only. The CLI does NOT spawn Claude or
any AI agent. It writes filesystem state that a human or AI tool reads later.

Architectural boundaries:
- pathly-engine/engine_cli/ must not import from pathly-adapters.
- No AI agent spawning from the CLI.
- doctor must not advance workflow state.

Expected file areas:
- pathly-engine/engine_cli/manager.py
- pathly-engine/engine_cli/__main__.py
- pathly-engine/pyproject.toml (scripts entry)
- tests/test_engine_cli.py

Verify:
- pathly go "add password reset"
- pathly status
- pathly doctor
- pytest tests/test_engine_cli.py -q

After done, update plans/pathly-two-project-split/PROGRESS.md phase 3 and story S3.1 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
```

**Expected output:** pathly go / status / doctor work from terminal. No AI tool required.
**Files touched:** engine_cli/ modules, pyproject.toml scripts entry, engine CLI tests.

---

## Conversation 4: Docs alignment

**Stories delivered:** S4.1

**Prompt to paste:**
```text
Implement pathly-two-project-split Conversation 4 from plans/pathly-two-project-split/IMPLEMENTATION_PLAN.md.

Scope — Phase 4: Docs alignment.

Update README and adapter docs to match verified behavior from Conversations 1-3.

Rules:
- Public beta language only. Do not claim production-ready.
- Keep Claude Code slash-command examples separate from Codex natural-language examples.
- Document only verified host behavior.
- pathly-adapters and pathly-engine are separate install commands — show both.

Expected file areas:
- README.md (root)
- pathly-adapters/README.md
- pathly-engine/README.md
- pathly-adapters/adapters/claude/README.md
- pathly-adapters/adapters/codex/README.md
- pathly-adapters/adapters/copilot/README.md
- tests/test_project_packaging.py (static alignment checks)

Do NOT touch install_cli/, engine_cli/, or orchestrator/ implementation except
for small fixes needed to align docs with actual behavior.

Verify:
- pytest -q
- Manual host smoke where available: pathly-setup claude --dry-run, /pathly help in Claude Code

After done, update plans/pathly-two-project-split/PROGRESS.md phase 4 and story S4.1 to DONE.
Change overall Status to COMPLETE if all conversations are DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
```

**Expected output:** Docs match verified behavior. Static alignment tests pass.
**Files touched:** README files, adapter docs, packaging tests.
