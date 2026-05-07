# clean-filesystem - Happy Flow

## Overview

The ideal migration starts from a green baseline and ends with a clean,
installable Pathly repository. Builders stabilize entrypoints first, add runner
and hook runtime modules, remove only verified legacy paths, and prove the
package contains all runtime and instruction assets.

## Step-by-Step Happy Flow

### Step 1: Stabilize entrypoints
- **Action:** Run Conversation 1.
- **Pathly does:** Canonical `pathly/cli/` and `pathly/team_flow/` packages
  become the executable entrypoints.
- **Repo state:** Local module execution and `pathly --help` work without tests
  depending on `scripts.team_flow`.

### Step 2: Add runner contract
- **Action:** Run Conversation 2.
- **Pathly does:** FSM runtime calls a shared runner interface with Claude,
  Codex, and auto selection.
- **Repo state:** Claude behavior remains compatible; Codex command construction
  is tested and usage fallback is documented.

### Step 3: Move hooks into runtime package
- **Action:** Run Conversation 3.
- **Pathly does:** Hook behavior is importable from `pathly/hooks/` and CLI
  commands can run hook events or print host config.
- **Repo state:** Root hook scripts are no longer required by runtime behavior,
  but remain until cleanup verification.

### Step 4: Delete verified legacy paths
- **Action:** Run Conversation 4 cleanup portion.
- **Pathly does:** Searches prove old imports and bridge references are gone
  before deleting legacy files.
- **Repo state:** Candidate modules, old shell installers, root hooks, and
  generated mirrors are absent or explicitly handled.

### Step 5: Prove package artifacts
- **Action:** Run Conversation 4 packaging gate.
- **Pathly does:** Build/install checks verify runtime packages and instruction
  assets ship together.
- **Repo state:** The cleaned filesystem can be installed and invoked through
  the public CLI.

## End State

Pathly has one canonical runtime shape, host-neutral runner selection, portable
hooks, no unverified legacy bridge files, and packaging tests that protect core
prompts, templates, adapters, plugin metadata, and runtime packages.

## Success Indicators

- [ ] `python -m pathly.cli --help` passes.
- [ ] `python -m pathly.team_flow --help` passes.
- [ ] `pathly --help` passes.
- [ ] `pytest -q` passes after each conversation.
- [ ] Cleanup search finds no remaining runtime references to deleted legacy
  paths.
- [ ] `python -m build` passes.
