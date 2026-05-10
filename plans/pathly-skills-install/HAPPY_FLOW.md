# pathly-skills-install — Happy Flow

## Overview
A user runs `pathly-setup --apply` on a machine with Claude Code installed.
The CLI installs both agents and skills in one command, writing 5 skill files to
`~/.claude/` alongside the existing 12 agents in `~/.claude/agents/`.

## Step-by-Step Happy Flow

### Step 1: CLI invoked
- **Action**: `pathly-setup --apply`
- **Setup command does**: calls `detect_hosts()` → returns `["claude"]`
- **State**: enters `_run_host("claude", dry_run=False, ...)`

### Step 2: Load install.yaml
- **Action**: read `adapters/claude/_meta/install.yaml`
- **Setup command does**: parses `destination`, `files`, and new `skills:` section
- **State**: `skills_cfg = {destination: ~/.claude/, structure: flat}`

### Step 3: Agent install (unchanged)
- **Action**: glob `*.yaml` in `_meta/` (excluding install.yaml and `*_skill.yaml`)
- **Setup command does**: calls `stitch_agent()` for each, passes to `materialize()`
- **State**: 12 agent files written to `~/.claude/agents/`

### Step 4: Skill discovery
- **Action**: glob `*_skill.yaml` in `_meta/`
- **Setup command does**: finds go_skill.yaml, start_skill.yaml, end_skill.yaml, help_skill.yaml, pause_skill.yaml
- **State**: 5 meta files queued for stitching

### Step 5: stitch_skill() per skill
- **Action**: for each skill YAML, call `stitch_skill(core_skills_path() / "go.md", meta)`
- **Stitch does**: reads core body, applies strip_frontmatter / wrapper rules, returns plain markdown
- **State**: 5 stitched content strings in `skill_files` dict

### Step 6: materialize() writes skills
- **Action**: `materialize(skill_files, Path("~/.claude/").expanduser(), ...)`
- **Materialize does**: writes go.md, start.md, end.md, help.md, pause.md; updates `.pathly-manifest.json`
- **State**: `~/.claude/go.md` etc. exist on disk

### Step 7: CLI reports
- **Action**: print summary
- **Output**: `[claude] Wrote 12 agent(s) to ~/.claude/agents/` then `[claude] Wrote 5 skill(s) to ~/.claude/`

## End State
- `~/.claude/agents/` has 12 stitched agent files
- `~/.claude/` has 5 stitched skill files (go.md, start.md, end.md, help.md, pause.md)
- `~/.claude/.pathly-manifest.json` tracks skill ownership
- User can type `/go` in Claude Code to invoke the go skill

## Success Indicators
- [ ] `pathly-setup --apply` exits 0
- [ ] `~/.claude/go.md` exists and contains go skill content
- [ ] `~/.claude/.pathly-manifest.json` has entries for all 5 skill filenames
- [ ] Existing agents in `~/.claude/agents/` are untouched
