# pathly-interface-redesign — Edge Cases

## Verb surface edge cases

### E1: `/pathly start` when a flow is already active
- Skill reads STATE.json and finds an active feature
- Prints: "Active flow found: `user-authentication` (state: BUILDING). Start a new feature anyway? [yes/no]"
- On yes: director starts fresh, new feature runs in parallel
- On no: suggests `/pathly continue`

### E2: `/pathly continue` with multiple active features
- Multiple `plans/*/STATE.json` files exist with recent modification times
- Skill shows numbered list: "[1] user-authentication (BUILDING) [2] payment-flow (PLANNING)"
- User picks one — orchestrator resumes that feature

### E3: `/pathly continue` with no STATE.json (only PROGRESS.md)
- Falls back to PROGRESS.md scan
- Finds the most recently modified plan folder
- Warns: "[FSM] No STATE.json — recovered from PROGRESS.md. State may be approximate."
- Continues from last TODO conversation

### E4: `/pathly end` when conversations are incomplete
- STATE.json shows BUILDING with 2 of 3 conversations TODO
- Warns: "Conversation 2 and 3 are not complete. End anyway? [yes/no]"
- On yes: retro runs, RETRO.md notes which conversations were skipped
- On no: suggests `/pathly continue`

### E5: `/pathly meet` with no active feature
- No `plans/` directory or all features are retro-done
- Prints: "No active flow. `/pathly start` to begin one."
- Does not crash or prompt for role

### E6: User types `/pathly start I want to build auth`
- Extra text after `start` is treated as intent hint
- Passed to director as pre-filled context: "User intent: I want to build auth"
- Director skips the "What do you want to build?" prompt

## Agent meta YAML edge cases

### E7: Meta YAML missing for an agent
- `pathly install` encounters a core agent file with no matching meta YAML
- Skips that agent, prints warning: "WARN: no meta for `discoverer` on platform `claude` — skipping"
- Does not abort the full install

### E8: Core agent file missing for a meta entry
- Meta YAML exists but `core/agents/{agent}.md` does not
- Skips that agent, prints warning: "WARN: core/agents/discoverer.md not found — skipping"
- Does not write a partial file

### E9: Meta YAML is malformed (invalid YAML)
- `pathly install --dry-run` parses all meta files first
- Reports: "ERROR: adapters/claude/_meta/architect.yaml line 7: mapping values are not allowed here"
- Aborts dry-run, does not write any files

### E10: `can_spawn` contains an unknown agent type
- Meta YAML has `can_spawn: [quick, scout, unknown-agent]`
- Installer warns: "WARN: architect can_spawn includes unknown type `unknown-agent`"
- Still writes the file — enforcement is by content (agent reads its own prompt), not by installer

### E11: Destination directory does not exist
- `~/.claude/agents/` does not exist
- Installer creates it: `mkdir -p ~/.claude/agents/`
- Continues stitching and writing

### E12: Destination file already exists (re-install or update)
- `~/.claude/agents/architect.md` already exists from a previous install
- Installer overwrites it
- Prints: "UPDATED: ~/.claude/agents/architect.md"

## Platform-specific edge cases

### E13: Copilot spawn syntax is not validated
- Copilot meta files use prose delegation (`/fleet`, `/delegate`)
- This syntax is experimental and not formally validated by the installer
- Meta files for Copilot are marked `status: experimental`
- Installer prints: "NOTE: copilot adapter is experimental — spawn syntax not validated"

### E14: `pathly install` run before `pip install pathly`
- User runs `pathly install` from a source checkout
- Installer resolves `core/agents/` relative to the script location
- Works correctly from source checkout and from installed wheel
