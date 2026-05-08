# installable-workflow-architecture - Happy Flow

## Overview

The ideal path is a new user installing Pathly, running a safe setup report,
applying host adapter setup only after reviewing planned writes, and then using
Pathly from their normal AI coding tool or the CLI. Pathly remains local,
inspectable, and file-backed throughout.

## Step-by-Step Happy Flow

### Step 1: Install Pathly
- **Action:** `pip install pathly`
- **Pathly does:** Installs the CLI entry point and packaged resource assets.
- **Workspace state:** No project files are modified.

### Step 2: Verify the installed package
- **Action:** `pathly --version`, `pathly --help`, `pathly doctor`
- **Pathly does:** Reports version, command surface, and local prerequisites.
- **Workspace state:** Missing Claude/Codex hosts are reported as host
  diagnostics, not install failures.

### Step 3: Review setup plan
- **Action:** `pathly setup --dry-run`
- **Pathly does:** Detects supported hosts, planned adapter writes, planned hook
  registration, conflicts, and final start commands.
- **Workspace state:** No files are written.

### Step 4: Apply setup explicitly
- **Action:** `pathly setup --apply`
- **Pathly does:** Copies packaged adapter assets into versioned user data
  snapshots and registers host-supported adapter locations.
- **Workspace state:** Only approved user-level Pathly data or host config files
  are written.

### Step 5: Start from the user's normal host
- **Action:** Claude Code `/pathly add password reset`, Codex `Use Pathly to add
  password reset`, or CLI `pathly go "add password reset"`.
- **Pathly does:** Routes through the Director/front door and keeps workflow
  state under `plans/<feature>/`.
- **Workspace state:** Plan files, feedback files, consult notes, state, and
  events remain inspectable on disk.

### Step 6: Recover after interruption
- **Action:** `pathly status [feature]` or `pathly doctor`
- **Pathly does:** Summarizes current state, open feedback, next owner, and the
  next safe command.
- **Workspace state:** No lifecycle state advances unless the user runs the next
  workflow command.

## End State

The user can install Pathly, understand what setup will do, apply adapter setup
safely, run the workflow from Claude Code, Codex, or CLI, and recover from
interruptions through file-backed state.

## Success Indicators

- [ ] Installed Pathly can load packaged core and adapter assets.
- [ ] Setup dry run writes no files.
- [ ] Setup apply writes only approved Pathly-owned locations.
- [ ] Status and doctor explain actionable recovery paths.
- [ ] Docs and smoke checks match the actual supported host behavior.
