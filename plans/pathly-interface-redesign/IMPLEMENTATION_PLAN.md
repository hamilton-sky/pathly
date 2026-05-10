# pathly-interface-redesign — Implementation Plan

## Overview

3 conversations. Conv 1 updates the skill surface (no-argument verbs). Conv 2 defines and populates agent meta YAML files. Conv 3 implements install-time stitching and the capability matrix.

**Dependency note:** Conv 3 of this plan should be coordinated with `installable-workflow-architecture` Conv 2 (adapter materialization). After this plan's Conv 3, the materializer copies stitched files instead of raw adapter files.

---

## Conversation 1 — No-argument verb surface (Stories S1.1–S2.2)

### Phase 1: Update `core/skills/pathly.md` verb router

- Remove argument-based routing (`flow <feature>`, `continue <feature>`, etc.)
- Add five no-argument verb routes: `start`, `continue`, `end`, `meet`, `help`
- `start` → route to director with no feature argument; director asks user
- `continue` → route to orchestrator; orchestrator reads STATE.json for active feature
- `end` → route to orchestrator; orchestrator confirms then triggers retro
- `meet` → route to `core/skills/meet.md` with no argument; meet reads STATE.json
- `help` → route to `core/skills/help.md` with no argument; help reads STATE.json
- Keep backward-compatible fallback: if first word is not a known verb, treat as intent and route to director

### Phase 2: Update `core/skills/help.md` menu to use `/pathly [verb]` syntax

- All numbered menu options print `/pathly [verb]` commands, not platform-specific syntax
- State: no-feature → shows `/pathly start`
- State: plan-done, build-in-progress → shows `/pathly continue`, `/pathly meet`, `/pathly help`
- State: feedback-open → shows `/pathly continue` (routes to correct agent automatically)
- State: build-done → shows `/pathly end`, `/pathly continue`
- State: retro-done → shows `/pathly start` (next feature), archive options

### Phase 3: Add `/pathly end` behavior to orchestrator routing

- `core/skills/pathly.md` routes `end` to team-flow retro entry
- Orchestrator confirms incomplete conversations before closing
- Retro runs, RETRO.md written

**Verify:** Manual smoke — type each verb and confirm correct routing. No argument parsing needed. `pytest tests/test_cli.py -q` if CLI tests cover skill routing.

**Recovery:** If routing is broken, `git checkout core/skills/pathly.md` and retry.

---

## Conversation 2 — Agent meta YAML format (Stories S3.1–S3.2)

### Phase 1: Define the meta YAML format

Define the canonical format for `adapters/{platform}/_meta/{agent}.yaml`:

```yaml
name: architect
description: Technical architecture design...
model: opus
tools: [Read, Glob, Grep, Write, Edit, Agent]
can_spawn: [quick, scout, web-researcher]

spawn_section: |
  ## Sub-agent invocation
  Agent(
    subagent_type="scout",
    model="haiku",
    ...
  )
```

- `name`, `description`: required — used as agent file frontmatter
- `model`: required — platform-specific model name
- `tools`: required for Claude Code — tool allowlist
- `can_spawn`: required — list of permitted sub-agent types (or `all` for orchestrator, `[]` for terminal)
- `spawn_section`: required — platform-specific spawn syntax block, written verbatim into stitched file

### Phase 2: Create meta YAML files for all agents — Claude adapter

Create `adapters/claude/_meta/` with one YAML per agent:
- architect, builder, director, discoverer, orchestrator, planner, po, quick, reviewer, scout, tester, web-researcher

Each file: minimal frontmatter + correct `can_spawn` per capability matrix + `spawn_section` with `Agent()` calls extracted from current adapter agent files.

### Phase 3: Create meta YAML files — Codex and Copilot adapters

Create `adapters/codex/_meta/` and `adapters/copilot/_meta/` with matching structure.
- Codex: `spawn_section` uses `spawn_agent` prose pattern
- Copilot: `spawn_section` uses `/fleet`/`/delegate` prose pattern, marked experimental

### Phase 4: Remove duplicated content from adapter agent files

- `adapters/claude/agents/*.md` — strip behavioral body, leave only a comment pointing to core and meta
- Or delete entirely if the installer will fully replace them
- `adapters/codex/agents/*.md` — same
- `adapters/copilot/agents/*.md` — same

**Do NOT touch** `core/agents/*.md` — these are the source of truth and are correct.

**Verify:** All meta YAML files parse without error: `python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('adapters/**/_meta/*.yaml', recursive=True)]"`. `can_spawn` values match the capability matrix in ARCHITECTURE_PROPOSAL.md.

**Recovery:** If YAML is malformed, `git checkout adapters/` and retry.

---

## Conversation 3 — Install-time stitching + capability matrix (Stories S4.1)

### Phase 1: Implement `pathly/cli/stitch.py`

New module — single responsibility: stitch core agent + meta YAML → complete agent file.

```python
def stitch_agent(core_path, meta_path) -> str:
    # 1. Read meta YAML
    # 2. Build frontmatter block from meta fields
    # 3. Read core agent body
    # 4. Build can_spawn section from meta['can_spawn']
    # 5. Append spawn_section from meta
    # Return: complete agent file content as string
```

Output structure:
```
---
name: architect
description: ...
model: opus
tools: [...]
---

## Capabilities
can_spawn: [quick, scout, web-researcher]

[core agent behavioral contract body]

## Sub-agent invocation
[spawn_section from meta YAML]
```

### Phase 2: Integrate stitcher into `pathly install`

Update `pathly/cli/setup_command.py` or `pathly/cli/manager.py`:
- For each platform in `adapters/`:
  - For each `adapters/{platform}/_meta/{agent}.yaml`:
    - Find matching `core/agents/{agent}.md`
    - Call `stitch_agent(core_path, meta_path)`
    - Write result to destination directory
- `--dry-run`: print what would be written, validate all YAMLs, do not write
- Report: N stitched, M warnings

### Phase 3: Add gitignore for generated adapter agent files

- Add `adapters/*/agents/` to `.gitignore` or move committed adapter agent files to `adapters/*/_generated/` (gitignored)
- The repo no longer tracks generated adapter agent files

### Phase 4: Update tests

- Add `tests/test_stitch.py` — tests for `stitch_agent()`:
  - Happy path: valid core + meta → correct output structure
  - Missing core file → warning, no output
  - Malformed YAML → clear error message
  - `can_spawn: all` → injected as "can spawn all agents"
  - `can_spawn: []` → injected as "TERMINAL — cannot spawn sub-agents"

**Verify:** `pytest tests/test_stitch.py -q`. `pathly install --dry-run` shows N agents stitched with no errors. Spot-check one stitched file at `~/.claude/agents/architect.md` — confirm it has frontmatter, core body, and spawn section.

**Recovery:** If stitching is broken, `git checkout pathly/cli/stitch.py` and retry. Destinations are written fresh each install — no rollback needed for destination files.
