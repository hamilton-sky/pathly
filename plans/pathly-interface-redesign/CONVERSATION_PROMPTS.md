# pathly-interface-redesign — Conversation Prompts

## Conversation 1: No-argument verb surface

Paste this prompt into a fresh Claude Code conversation:

---

You are implementing the no-argument verb surface for Pathly. This is Conversation 1 of the `pathly-interface-redesign` plan. Read `plans/pathly-interface-redesign/IMPLEMENTATION_PLAN.md` and `plans/pathly-interface-redesign/ARCHITECTURE_PROPOSAL.md` before making any changes.

**What to implement (Phases 1–3):**

**Phase 1 — Update `core/skills/pathly.md`:**
Replace the current argument-based routing with five no-argument verb routes:
- `start` → route to director agent with no feature argument; director will ask the user for intent
- `continue` → route to orchestrator; orchestrator reads `plans/*/STATE.json` to find the active feature (most recently modified)
- `end` → route to orchestrator; orchestrator confirms with user, then routes to retro entry of team-flow
- `meet` → route to `core/skills/meet.md` with no argument; meet.md already reads STATE.json for active feature
- `help` → route to `core/skills/help.md` with no argument; help.md already reads STATE.json

Keep a backward-compatible fallback: if the first word is not one of the five verbs, treat the full text as plain-English intent and route to director (same as `start` with pre-filled intent).

**Phase 2 — Update `core/skills/help.md` menu options:**
All numbered menu options in the state menus must use `/pathly [verb]` syntax. Replace any platform-specific command references. States to update:
- no-feature → `/pathly start`
- plan-done → `/pathly continue`, `/pathly meet`, `/pathly help`
- feedback-open → `/pathly continue`
- build-done → `/pathly end`, `/pathly continue`
- retro-done → `/pathly start`

**Phase 3 — Add end verb behavior:**
In `core/skills/pathly.md`, the `end` route must:
1. Route to team-flow retro entry (`team-flow <feature> test` if not tested, or retro directly if tested)
2. The orchestrator reads STATE.json to determine which retro path is needed
3. If conversations are incomplete: orchestrator warns and asks confirmation before closing

**Do NOT touch** `adapters/`, `core/agents/`, or any Python files. Those are Conv 2 and Conv 3.

**Verify when done:**
- Manually confirm: each of the five verbs produces the expected routing behavior when you read `core/skills/pathly.md`
- Confirm `core/skills/help.md` menus only reference `/pathly [verb]` commands
- Run: `pytest tests/test_cli.py -q` (if skill routing tests exist)

**Recovery:** If verification fails and fix requires out-of-scope changes, stop and report. If fundamentally broken, `git checkout core/skills/pathly.md core/skills/help.md` and retry.

Update `plans/pathly-interface-redesign/PROGRESS.md` — mark Conv 1 DONE and all S1.1–S2.2 stories DONE after verification passes.

---

## Conversation 2: Agent meta YAML format

Paste this prompt into a fresh Claude Code conversation after Conv 1 is committed:

---

You are implementing the agent meta YAML format for Pathly. This is Conversation 2 of the `pathly-interface-redesign` plan. Read `plans/pathly-interface-redesign/IMPLEMENTATION_PLAN.md` and `plans/pathly-interface-redesign/ARCHITECTURE_PROPOSAL.md` before making any changes. Conv 1 is complete — do not touch `core/skills/`.

**What to implement (Phases 4–7):**

**Phase 4 — Meta YAML format:**
The canonical format for `adapters/{platform}/_meta/{agent}.yaml` is:

```yaml
name: architect
description: Technical architecture design, layer decisions...
model: opus
tools: [Read, Glob, Grep, Write, Edit, Agent]
can_spawn: [quick, scout, web-researcher]

spawn_section: |
  ## Sub-agent invocation
  [platform-specific spawn syntax here]
```

Fields: `name`, `description`, `model` (platform-specific), `tools` (Claude only), `can_spawn` (list or `all` or `[]`), `spawn_section` (verbatim block written into stitched file).

**Phase 5 — Create `adapters/claude/_meta/*.yaml` for all 12 agents:**
Read the current `adapters/claude/agents/*.md` files to extract the existing spawn sections and frontmatter. Create one YAML per agent. Use the capability matrix from ARCHITECTURE_PROPOSAL.md for `can_spawn` values:
- orchestrator: `can_spawn: all`
- director: `can_spawn: [orchestrator, architect, po, web-researcher]`
- builder: `can_spawn: [quick, scout]`
- reviewer: `can_spawn: [quick, scout]`
- architect: `can_spawn: [quick, scout, web-researcher]`
- planner: `can_spawn: [quick, scout]`
- tester: `can_spawn: [quick, scout]`
- po, web-researcher: `can_spawn: []`
- scout, quick: `can_spawn: []` (TERMINAL)

**Phase 6 — Create `adapters/codex/_meta/*.yaml` and `adapters/copilot/_meta/*.yaml`:**
Same structure. Codex `spawn_section` uses prose delegation pattern. Copilot `spawn_section` uses prose delegation, add `status: experimental` field. Read existing adapter agent files for current spawn patterns.

**Phase 7 — Strip duplicated content from adapter agent files:**
For each `adapters/*/agents/{agent}.md`, replace the full content with a short redirect comment:
```markdown
<!-- Generated by pathly install. Edit adapters/{platform}/_meta/{agent}.yaml instead. -->
<!-- Source: core/agents/{agent}.md -->
```
Or delete these files entirely if the `.gitignore` approach is preferred (ask yourself: which is cleaner?).

**Do NOT touch** `core/agents/`, `core/skills/`, or any Python files. Those are out of scope.

**Verify when done:**
```python
python -c "
import yaml, glob
files = glob.glob('adapters/**/_meta/*.yaml', recursive=True)
for f in files:
    yaml.safe_load(open(f))
    print(f'OK: {f}')
print(f'Total: {len(files)} meta files validated')
"
```
Confirm `can_spawn` values match ARCHITECTURE_PROPOSAL.md capability matrix for at least architect, builder, and orchestrator.

**Recovery:** If YAML parse fails, `git checkout adapters/` and retry.

Update `plans/pathly-interface-redesign/PROGRESS.md` — mark Conv 2 DONE and S3.1, S3.2 DONE after verification passes.

---

## Conversation 3: Install-time stitching

Paste this prompt into a fresh Claude Code conversation after Conv 2 is committed:

---

You are implementing install-time agent stitching for Pathly. This is Conversation 3 of the `pathly-interface-redesign` plan. Read `plans/pathly-interface-redesign/IMPLEMENTATION_PLAN.md` and `plans/pathly-interface-redesign/ARCHITECTURE_PROPOSAL.md` before making any changes. Conv 1 and Conv 2 are complete.

**What to implement (Phases 8–11):**

**Phase 8 — Create `pathly/cli/stitch.py`:**
New module with one public function:

```python
def stitch_agent(core_path: Path, meta_path: Path) -> str:
    """Read core agent md + meta YAML, return complete stitched agent file content."""
```

Output structure (in order):
1. YAML frontmatter block — fields from meta: name, description, model, tools, skills (if present)
2. Blank line
3. `## Capabilities` section with `can_spawn` rendered as human-readable text
4. Blank line
5. Full text of `core_path` (behavioral contract)
6. Blank line
7. `spawn_section` from meta YAML

For `can_spawn: all` → render as "This agent may spawn any other agent type."
For `can_spawn: []` → render as "TERMINAL — this agent may not spawn sub-agents."
For `can_spawn: [quick, scout]` → render as "This agent may spawn: quick, scout."

**Phase 9 — Integrate stitcher into `pathly install`:**
Find the existing install/setup command (`pathly/cli/setup_command.py` or similar). Add a stitch step:
- For each `adapters/{platform}/_meta/*.yaml`:
  - Find matching `core/agents/{agent}.md` (where agent = YAML `name` field)
  - Call `stitch_agent()`
  - Write result to the platform's destination directory
  - Collect warnings for missing core files or meta files
- Add `--dry-run` flag: validate all YAMLs, print what would be written, write nothing
- Print summary: "Stitched N agents → {destination}. Warnings: M."

**Phase 10 — Gitignore generated adapter agent files:**
Add to `.gitignore`:
```
adapters/*/agents/*.md
```
Or if you chose the redirect-comment approach in Conv 2, add the `_generated/` directories instead.

**Phase 11 — Add `tests/test_stitch.py`:**
Tests for the stitcher:
- Happy path: valid core md + valid meta YAML → output contains frontmatter, can_spawn section, core body, spawn_section
- Missing core file → `FileNotFoundError` or warning return, no partial output
- Malformed YAML → `yaml.YAMLError` raised with useful message
- `can_spawn: all` → output contains "may spawn any other agent type"
- `can_spawn: []` → output contains "TERMINAL"

**Do NOT touch** `core/agents/`, `core/skills/`, or any adapter meta YAML files.

**Verify when done:**
```bash
pytest tests/test_stitch.py -q
pathly install --dry-run
```
Spot-check: run `pathly install --dry-run` and confirm it lists all 11+ agents across platforms with no errors.

**Recovery:** If stitcher is broken, `git checkout pathly/cli/stitch.py tests/test_stitch.py` and retry. Destination files are written fresh on each install — no rollback needed.

Update `plans/pathly-interface-redesign/PROGRESS.md` — mark Conv 3 DONE and S4.1 DONE after verification passes.
