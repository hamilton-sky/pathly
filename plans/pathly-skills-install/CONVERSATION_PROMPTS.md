# pathly-skills-install — Conversation Guide

Split into 3 conversations. Each leaves the codebase runnable.
After each conversation, **commit your changes** before starting the next.

---

## Conversation 1: Skill install engine (Phases 1-2)

**Stories delivered:** S1.1, S1.2

**Prompt to paste:**
```
Implement pathly-skills-install Conversation 1 (Phases 1-2) from
plans/pathly-skills-install/IMPLEMENTATION_PLAN.md.

Working directory for all paths: pathly-adapters/

Scope:

Phase 1 — stitch_skill() + resources:
- Add `stitch_skill(core_path: Path, meta_path: Path) -> str` to
  `install_cli/stitch.py` alongside the existing `stitch_agent()`.
  Required YAML fields: `skill` (str, core file stem), `invocation` (str).
  Optional: `strip_frontmatter` (bool), `wrapper` (str), `natural_language` (str),
  `filename` (str).
  Logic:
    1. Load YAML; raise ValueError for missing required fields or malformed YAML.
    2. If `wrapper` is set, use wrapper as the body (core_path is not read;
       FileNotFoundError is suppressed even if core_path is missing).
    3. Otherwise read core_path (raise FileNotFoundError if missing).
    4. If `strip_frontmatter: true`, strip the leading ---...--- block from the body.
    5. Return plain markdown string — do NOT inject YAML frontmatter (skills have
       no frontmatter, unlike agents).
- Add `core_skills_path() -> Path` to `install_cli/resources.py`:
  returns `_root() / "core" / "skills"`.

Phase 2 — install.yaml + _run_host() wiring:
- Add a `skills:` section to each adapter's install.yaml:
    adapters/claude/_meta/install.yaml  → skills: {destination: ~/.claude/, structure: flat}
    adapters/codex/_meta/install.yaml   → skills: {destination: ~/.codex/, structure: flat}
    adapters/copilot/_meta/install.yaml → skills: {destination: ~/.vscode/extensions/pathly/skills/, structure: flat}
- In `install_cli/setup_command.py`, inside `_run_host()`, after the existing
  agent materialize block, add a skill install block:
    - Read `install_cfg.get("skills")`; if absent, skip silently.
    - Discover skill YAMLs by globbing `meta_dir.glob("*_skill.yaml")`.
    - For each: call `stitch_skill(core_skills_path() / f"{skill_meta['skill']}.md", meta_file)`.
      Catch FileNotFoundError → print warn to stderr, skip that skill.
    - Use `skill_meta.get("filename", f"{skill_name}.md")` as the output filename
      (skill_name = meta_file.stem with `_skill` suffix removed).
    - Pass collected dict to `materialize(skill_files, skills_dest, ...)`.
    - In dry-run mode: print would-write skill filenames under skills_dest.
  Import `stitch_skill` and `core_skills_path` at the top of setup_command.py.

Architecture boundaries:
- stitch_skill() must not import from setup_command.py (one-way dependency).
- materialize() is reused as-is — do not modify it.
- Do NOT touch core/skills/ files, any agent YAML files, or tests yet.

Verify:
1. cd pathly-adapters && pytest tests/test_stitch.py -x   (existing tests must pass)
2. pathly-setup --dry-run   (must run without error; no skill lines yet since no *_skill.yaml exist)

After done, update plans/pathly-skills-install/PROGRESS.md phases 1-2 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** `stitch_skill()` importable, `core_skills_path()` works, `--dry-run` runs cleanly showing agents only, all install.yaml files have `skills:` section
**Files touched:** `install_cli/stitch.py`, `install_cli/resources.py`, `install_cli/setup_command.py`, `adapters/claude/_meta/install.yaml`, `adapters/codex/_meta/install.yaml`, `adapters/copilot/_meta/install.yaml`

---

## Conversation 2: Skill bodies + YAML metadata for all adapters (Phases 3-5)

**Stories delivered:** S2.1, S2.2, S2.3

**Prompt to paste:**
```
Implement pathly-skills-install Conversation 2 (Phases 3-5) from
plans/pathly-skills-install/IMPLEMENTATION_PLAN.md.

Conversation 1 is complete: stitch_skill(), core_skills_path(), skills: sections in
install.yaml, and skill loop in _run_host() are all done.

Working directory for all paths: pathly-adapters/

Scope:

Phase 3 — New core skill bodies:
- Create `core/skills/start.md`:
  Director entry point. Greets the user, explains it can route to:
    (1) /storm — brainstorm / shape an idea
    (2) /plan  — define a feature from a description
    (3) /go    — continue in-progress work
    (4) /prd-import — import a PRD file
  Asks "What do you want to do?" and waits. Routes to the chosen skill.
  Keep it concise (~30 lines): a short greeting, the four numbered options, and a
  wait-for-input instruction.

- Create `core/skills/end.md`:
  Session wrap-up. Steps:
    1. Check if any feature in plans/ has PROGRESS.md with status IN PROGRESS.
    2. If found, print a completion summary (feature name, conversations done/total).
    3. Ask "Write a retro? (y/n)". If yes, invoke /retro <feature>. If no, print
       "All done. Changes committed? Run git commit if not."
    4. If no in-progress feature found, print "Nothing in progress. All done."

Phase 4 — Claude skill YAML metadata (5 files):
Create adapters/claude/_meta/<name>_skill.yaml for: go, start, end, help, pause.

go_skill.yaml:
  skill: go
  filename: go.md
  invocation: /go
  natural_language: "go, continue, next step, keep going, resume"

start_skill.yaml:
  skill: start
  filename: start.md
  invocation: /start
  natural_language: "start, begin, new session, wake up"

end_skill.yaml:
  skill: end
  filename: end.md
  invocation: /end
  natural_language: "end, finish, wrap up, done, exit"

help_skill.yaml:
  skill: help
  filename: help.md
  invocation: /help
  natural_language: "help, what can you do, show commands"

pause_skill.yaml:
  skill: pause
  filename: pause.md
  invocation: /pause
  natural_language: "pause, stop for now, save and exit"
  wrapper: |
    Write `status: PAUSED` to the current feature's PROGRESS.md (if one exists in plans/).
    Then print: "Session paused. Resume with /go when ready."

Phase 5 — Codex and Copilot skill YAML metadata (10 files total):

Codex: same structure as Claude but invocation: @<name> (e.g., @go, @start).
Create adapters/codex/_meta/{go,start,end,help,pause}_skill.yaml.

Copilot: invocation: "#pathly" for all 5 (placeholder — Copilot prefix spec TBD).
Add a YAML comment on the invocation line: # TODO: confirm Copilot prefix spec
Create adapters/copilot/_meta/{go,start,end,help,pause}_skill.yaml.
Copilot pause_skill.yaml uses the same wrapper content as claude.

Architecture boundaries:
- Do NOT modify stitch.py, resources.py, setup_command.py, or materialize.py.
- Do NOT touch agent YAML files (*.yaml without _skill suffix in _meta/).
- Do NOT create tests yet.

Verify:
1. pathly-setup --dry-run   should show 5 would-write skill lines per detected host
2. cd pathly-adapters && pytest tests/test_stitch.py -x   (must still pass)

After done, update plans/pathly-skills-install/PROGRESS.md phases 3-5 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** 2 new core skill bodies, 15 new skill YAML files (5 × 3 adapters), `--dry-run` shows skill install lines
**Files touched:** `core/skills/start.md`, `core/skills/end.md`, `adapters/claude/_meta/*_skill.yaml` (×5), `adapters/codex/_meta/*_skill.yaml` (×5), `adapters/copilot/_meta/*_skill.yaml` (×5)

---

## Conversation 3: Tests (Phase 6)

**Stories delivered:** S3.1

**Prompt to paste:**
```
Implement pathly-skills-install Conversation 3 (Phase 6) from
plans/pathly-skills-install/IMPLEMENTATION_PLAN.md.

Conversations 1 and 2 are complete: stitch_skill() exists in install_cli/stitch.py,
core/skills/start.md and end.md exist, and all 15 *_skill.yaml files exist across
the three adapters.

Working directory: pathly-adapters/

Scope:

Phase 6 — Tests for stitch_skill():
Create `tests/test_stitch_skill.py` mirroring the structure of `tests/test_stitch.py`.

Test cases to implement (use pytest fixtures and tmp_path):

1. test_stitch_skill_returns_plain_body — happy path with core + meta, result does
   NOT start with "---" (no frontmatter injected)

2. test_stitch_skill_wrapper_used_when_set — wrapper field in YAML → result equals
   wrapper content; core_path may or may not exist (test without creating core file)

3. test_stitch_skill_strip_frontmatter — core file has ---\nkey: val\n---\nBody.
   With strip_frontmatter: true → "key: val" not in result, "Body." in result

4. test_stitch_skill_no_strip_by_default — same core file without strip_frontmatter
   → frontmatter block preserved in output

5. test_stitch_skill_missing_required_fields_raises — YAML missing `invocation` →
   raises ValueError with "Missing required fields"

6. test_stitch_skill_malformed_yaml_raises — bad YAML → raises ValueError with
   "Malformed YAML"

7. test_stitch_skill_missing_core_no_wrapper_raises — core file does not exist and
   no wrapper → raises FileNotFoundError

8. test_stitch_skill_real_go_claude — smoke test using real files:
   core = core_skills_path() / "go.md"
   meta = adapter_meta_path("claude") / "go_skill.yaml"
   Skip if either missing. Assert result contains content from go.md, no "---" header.

Architecture boundaries:
- Do NOT modify stitch.py, resources.py, setup_command.py, or any YAML files.
- Do NOT write integration tests that invoke pathly-setup as a subprocess (unit tests only).

Verify:
cd pathly-adapters && pytest -x

After done, update plans/pathly-skills-install/PROGRESS.md phase 6 to DONE and
overall Status to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** `tests/test_stitch_skill.py` with 8 tests, all passing
**Files touched:** `tests/test_stitch_skill.py`
