# pathly-skills-install — User Stories

## Context
`pathly-setup` currently installs agents via a YAML-driven stitch pipeline. Skills
(slash commands, at-commands, hash-commands) are not yet installed. This feature
extends the same YAML pattern to skills, adds five canonical commands (go, start,
end, help, pause), and wires everything into the existing `_run_host()` flow so one
`pathly-setup --apply` installs both agents and skills.

## Stories

### Story 1.1: stitch_skill() function
**As a** Pathly maintainer, **I want** a `stitch_skill(core_path, meta_path)` function
that mirrors `stitch_agent()`, **so that** skill files are assembled from a core body
plus adapter-specific YAML metadata without duplicating install logic.

**Acceptance Criteria:**
- [ ] `stitch_skill()` reads the core `.md` file and the skill YAML
- [ ] Required YAML fields: `skill` (core file stem), `invocation`
- [ ] Optional: `strip_frontmatter`, `wrapper`, `natural_language`, `filename`
- [ ] If `wrapper` is set, it replaces the core body (enables alias-style skills like pause)
- [ ] If `strip_frontmatter` is true, `---...---` blocks are removed from the core body
- [ ] Missing core file raises `FileNotFoundError` (unless `wrapper` is set)
- [ ] Missing required fields raises `ValueError`

**Edge Cases:**
- Core file missing but `wrapper` provided → use wrapper, no error
- `strip_frontmatter: true` on file with no frontmatter → no-op, body returned unchanged

**Delivered by:** Phase 1 → Conversation 1

---

### Story 1.2: Skills section in install.yaml + _run_host() wiring
**As a** Pathly user, **I want** `pathly-setup --apply` to install skills alongside
agents, **so that** one command sets up the full AI host surface.

**Acceptance Criteria:**
- [ ] Each adapter's `install.yaml` has a `skills:` key with `destination` and `structure`
- [ ] `_run_host()` reads `skills:` from install.yaml and calls skill install when present
- [ ] Skill YAMLs are discovered by `*_skill.yaml` glob in `_meta/` (distinct from `*.yaml` agents)
- [ ] Skills are written via the existing `materialize()` function (ownership tracked per-dest)
- [ ] `--dry-run` shows would-write skill filenames
- [ ] If no skill YAMLs exist for a host, skill step is skipped silently

**Edge Cases:**
- Host has `install.yaml` with no `skills:` key → agent-only install, no crash
- Skill YAML points to missing core file AND no wrapper → warn and skip (don't abort)

**Delivered by:** Phase 2 → Conversation 1

---

### Story 2.1: Canonical skill bodies — start and end
**As a** Pathly user, **I want** `start` and `end` to exist as installable skill
bodies, **so that** adapters can install them with the same stitch pipeline used for go
and help.

**Acceptance Criteria:**
- [ ] `core/skills/start.md` created: wakes Director, asks storm/PO/plan/import-PRD
- [ ] `core/skills/end.md` created: prompts "Write a retro? y/n", runs `/retro` if yes

**Edge Cases:**
- `start` called with no active feature → Director should ask what to build
- `end` called when retro already exists → ask to overwrite or skip

**Delivered by:** Phase 3 → Conversation 2

---

### Story 2.2: Skill YAML metadata — Claude adapter (5 skills)
**As a** Claude Code user, **I want** go, start, end, help, and pause installed as
`~/.claude/` skill files, **so that** I can invoke them with `/go`, `/start`, etc.

**Acceptance Criteria:**
- [ ] `adapters/claude/_meta/{go,start,end,help,pause}_skill.yaml` created
- [ ] Each YAML has `invocation: /<name>`, `natural_language` hint
- [ ] `pause` uses `wrapper` field (3-line alias body, no core file)
- [ ] `--dry-run` shows 5 would-write files for claude skills dest

**Edge Cases:**
- pause wrapper content must stand alone (no core file required)

**Delivered by:** Phase 4 → Conversation 2

---

### Story 2.3: Skill YAML metadata — Codex and Copilot adapters (5 skills each)
**As a** Codex / Copilot user, **I want** the same 5 commands installed for my host,
**so that** Pathly works across all supported AI tools.

**Acceptance Criteria:**
- [ ] `adapters/codex/_meta/{go,start,end,help,pause}_skill.yaml` with `invocation: @<name>`
- [ ] `adapters/copilot/_meta/{go,start,end,help,pause}_skill.yaml` with `invocation: #pathly` (placeholder — see TODO in YAML)
- [ ] Copilot uses `structure: flat` in install.yaml skills section
- [ ] `--dry-run` shows would-write skill files for codex and copilot

**Delivered by:** Phase 5 → Conversation 2

---

### Story 3.1: Tests for stitch_skill()
**As a** maintainer, **I want** `stitch_skill()` covered by unit tests mirroring
`test_stitch.py`, **so that** skill assembly regressions are caught early.

**Acceptance Criteria:**
- [ ] `tests/test_stitch_skill.py` created
- [ ] Tests cover: happy path, wrapper-only (no core), strip_frontmatter, missing required fields, malformed YAML, missing core without wrapper
- [ ] Smoke test exercises a real skill file (go + claude skill YAML)
- [ ] `pytest -x` passes from `pathly-adapters/`

**Delivered by:** Phase 6 → Conversation 3
