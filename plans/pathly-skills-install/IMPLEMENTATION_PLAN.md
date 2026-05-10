# pathly-skills-install — Implementation Plan

## Overview
Extend `pathly-setup` to install skills alongside agents using the same YAML-driven
stitch pattern. Adds `stitch_skill()`, a `skills:` section to each adapter's
`install.yaml`, per-adapter skill YAML metadata for 5 canonical commands, two new
core skill bodies (start, end), and full unit test coverage for the new function.

## Layer Architecture

```
install.yaml (skills: section)
     │  destination, structure
     ▼
_run_host() in setup_command.py
     │  globs *_skill.yaml from _meta/
     ▼
stitch_skill(core_path, meta_path)
     │  reads core/skills/<name>.md + adapter YAML
     ▼
materialize(skill_files, skills_dest)
     │  writes files, updates .pathly-manifest.json
     ▼
~/.claude/<name>.md  |  ~/.codex/<name>.md  |  ~/.vscode/.../<name>.md
```

## Phases

### Phase 1: stitch_skill() + resources (Conv 1, ~30 min)
**Layer:** install_cli
**Delivers stories:** S1.1
**Files:**
- `pathly-adapters/install_cli/stitch.py` — add `stitch_skill(core_path, meta_path) -> str`
- `pathly-adapters/install_cli/resources.py` — add `core_skills_path() -> Path`

**Details:**
```python
def stitch_skill(core_path: Path, meta_path: Path) -> str:
    # Load YAML; required: skill, invocation
    # If wrapper set and core_path missing → use wrapper body
    # If wrapper set and core_path present → use wrapper (wrapper wins)
    # If strip_frontmatter: true → strip leading ---...--- block from body
    # Return plain markdown string (no frontmatter injected — skills are bodyonly)
```
`strip_frontmatter` strips the first `---\n...\n---\n` block if present.
`core_skills_path()` returns `_root() / "core" / "skills"`.

**Verify:** `cd pathly-adapters && pytest tests/test_stitch.py -x` (existing tests still pass)

---

### Phase 2: install.yaml + _run_host() wiring (Conv 1, ~30 min)
**Layer:** install_cli + adapter config
**Delivers stories:** S1.2
**Files:**
- `pathly-adapters/adapters/claude/_meta/install.yaml` — add `skills:` section
- `pathly-adapters/adapters/codex/_meta/install.yaml` — add `skills:` section
- `pathly-adapters/adapters/copilot/_meta/install.yaml` — add `skills:` section
- `pathly-adapters/install_cli/setup_command.py` — add skill install block in `_run_host()`

**Details:**
Claude install.yaml addition:
```yaml
skills:
  destination: ~/.claude/
  structure: flat
```
Codex: `destination: ~/.codex/`, Copilot: `destination: ~/.vscode/extensions/pathly/skills/`

In `_run_host()`, after existing agent block:
```python
skills_cfg = install_cfg.get("skills")
if skills_cfg:
    skills_dest = Path(skills_cfg["destination"]).expanduser()
    core_skills_dir = core_skills_path()
    skill_files: dict[str, str] = {}
    for meta_file in sorted(meta_dir.glob("*_skill.yaml")):
        skill_name = meta_file.stem.removesuffix("_skill")
        skill_meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        core_file = core_skills_dir / f"{skill_meta['skill']}.md"
        try:
            skill_files[skill_meta.get("filename", f"{skill_name}.md")] = stitch_skill(core_file, meta_file)
        except FileNotFoundError:
            print(f"  [warn] No core skill for {skill_name!r}, skipping", file=sys.stderr)
    if dry_run:
        print(f"\n[{host}] Would write skills to {skills_dest}:")
        for name in sorted(skill_files):
            print(f"  {skills_dest / name}")
    else:
        written = materialize(skill_files, skills_dest, repair=repair, force=force, dry_run=False)
        if written:
            print(f"[{host}] Wrote {len(written)} skill(s) to {skills_dest}")
```

**Verify:** `pathly-setup --dry-run` runs without error; shows agent lines, no skill lines yet (no *_skill.yaml files exist)

---

### Phase 3: core/skills/start.md and core/skills/end.md (Conv 2, ~20 min)
**Layer:** core skills
**Delivers stories:** S2.1
**Files:**
- `pathly-adapters/core/skills/start.md` — Director entry, asks what to do
- `pathly-adapters/core/skills/end.md` — optional retro prompt

**Details:**
`start.md` content: wake Director, offer four routes: storm / PO session / straight to plan / import PRD. Print a short menu and wait for user selection.
`end.md` content: check if a RETRO.md exists for the current feature, print completion summary, ask "Write a retro? (y/n)", invoke `/retro <feature>` if yes.

**Verify:** Files exist at correct paths; `cat pathly-adapters/core/skills/start.md` shows the Director menu

---

### Phase 4: Claude skill YAML metadata (Conv 2, ~20 min)
**Layer:** adapters/claude/_meta
**Delivers stories:** S2.2
**Files (5 new):**
- `pathly-adapters/adapters/claude/_meta/go_skill.yaml`
- `pathly-adapters/adapters/claude/_meta/start_skill.yaml`
- `pathly-adapters/adapters/claude/_meta/end_skill.yaml`
- `pathly-adapters/adapters/claude/_meta/help_skill.yaml`
- `pathly-adapters/adapters/claude/_meta/pause_skill.yaml`

**Details:**
All have `invocation: /<name>`. `pause_skill.yaml` uses `wrapper` (no core file):
```yaml
skill: pause
filename: pause.md
invocation: /pause
natural_language: "pause, stop for now, save and exit"
wrapper: |
  Write `status: PAUSED` to the current feature's PROGRESS.md (if one exists).
  Then print: "Session paused. Resume with /go when ready."
```
Others use `skill: go` (etc.) pointing to the matching core file.

**Verify:** `pathly-setup --dry-run` shows 5 would-write skill filenames under `~/.claude/`

---

### Phase 5: Codex and Copilot skill YAML metadata (Conv 2, ~20 min)
**Layer:** adapters/codex/_meta, adapters/copilot/_meta
**Delivers stories:** S2.3
**Files (10 new):**
- `pathly-adapters/adapters/codex/_meta/{go,start,end,help,pause}_skill.yaml`
- `pathly-adapters/adapters/copilot/_meta/{go,start,end,help,pause}_skill.yaml`

**Details:**
Codex: `invocation: @<name>`. Copilot: `invocation: "#pathly"` with a YAML comment
`# TODO: confirm Copilot prefix spec when available`. All pause YAMLs use same wrapper
pattern as claude.

**Verify:** `pathly-setup --dry-run` shows would-write skill lines for codex and copilot hosts

---

### Phase 6: Tests for stitch_skill() (Conv 3, ~30 min)
**Layer:** tests
**Delivers stories:** S3.1
**Files:**
- `pathly-adapters/tests/test_stitch_skill.py` — new test file

**Details:**
Mirror `test_stitch.py` structure. Test cases:
1. Happy path: core + meta → returns plain body (no `---` at start)
2. wrapper-only (core file absent) → returns wrapper content
3. strip_frontmatter: true → `---` block removed from output
4. Missing required fields → `ValueError`
5. Malformed YAML → `ValueError`
6. Core missing, no wrapper → `FileNotFoundError`
7. Smoke test: real go.md + claude go_skill.yaml → body contains go content

**Verify:** `cd pathly-adapters && pytest -x` — all tests pass

---

## Prerequisites
- `stitch_agent()` and `materialize()` already implemented (done)
- `core/skills/` directory with 18 skill bodies already exists (done)
- `adapters/<host>/_meta/` directories with agent YAMLs already exist (done)

## Key Decisions
- **No frontmatter injected into skills** — skills are plain markdown bodies; adapters don't need YAML headers (unlike agents which use frontmatter for model/tools)
- **wrapper wins over core** — if both are specified, wrapper is used; this prevents accidental leakage of platform-agnostic bodies into platform-specific adapters
- **Skills tracked per-dest** — reuses existing `materialize()` with `.pathly-manifest.json` next to each skill destination; no central manifest in this plan
- **pause is wrapper-only** — 3 lines of logic, no full .md file; `FileNotFoundError` suppressed when wrapper is present
- **Copilot prefix is placeholder** — `#pathly` with explicit TODO comment; full spec deferred
