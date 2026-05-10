# pathly-skills-install — Edge Cases

## Category 1: Missing Files

### EC-1.1: Skill YAML points to non-existent core file (no wrapper)
- **Trigger**: `go_skill.yaml` has `skill: go` but `core/skills/go.md` doesn't exist
- **Current behavior**: would raise FileNotFoundError and abort host install
- **Expected behavior**: print `[warn] No core skill for 'go', skipping` to stderr; continue with other skills
- **Handled in**: Phase 2 — FileNotFoundError caught in `_run_host()` skill loop

### EC-1.2: No `*_skill.yaml` files found for a host
- **Trigger**: Claude adapter has no `*_skill.yaml` files yet (e.g., Conv 1 before Conv 2 runs)
- **Expected behavior**: skill step produces no output, no error; agent install proceeds normally
- **Handled in**: Phase 2 — empty glob result → empty `skill_files` dict → `materialize()` writes nothing

### EC-1.3: `install.yaml` has no `skills:` key
- **Trigger**: older adapter install.yaml not yet updated
- **Expected behavior**: `install_cfg.get("skills")` returns None → skip skill block entirely
- **Handled in**: Phase 2 — `if skills_cfg:` guard

---

## Category 2: Wrapper Behaviour

### EC-2.1: `wrapper` set with core file also present
- **Trigger**: YAML has both `skill: go` and `wrapper: "..."` with go.md existing
- **Expected behavior**: wrapper wins; core file is NOT read
- **Handled in**: Phase 1 — `if wrapper: use wrapper` check happens before `core_path.read_text()`

### EC-2.2: `wrapper` set, core file absent (pause use-case)
- **Trigger**: `pause_skill.yaml` has `wrapper` set; no `core/skills/pause.md` exists
- **Expected behavior**: wrapper body returned, no FileNotFoundError
- **Handled in**: Phase 1 — core read path skipped when wrapper is set

---

## Category 3: strip_frontmatter Edge Cases

### EC-3.1: `strip_frontmatter: true` but body has no `---` block
- **Trigger**: core skill file has no YAML frontmatter
- **Expected behavior**: body returned unchanged, no error
- **Handled in**: Phase 1 — strip logic is a no-op if no `---` block found

### EC-3.2: `strip_frontmatter: false` (or absent) with frontmatter in body
- **Trigger**: go.md has a leading `---` block; `strip_frontmatter` not set
- **Expected behavior**: frontmatter block kept in output
- **Handled in**: Phase 1 — default behaviour, no stripping

---

## Category 4: Cross-host and Ownership

### EC-4.1: Skill file already exists at destination, not Pathly-owned
- **Trigger**: user has a custom `~/.claude/go.md` from another tool
- **Expected behavior**: `materialize()` skips (not owned, no `--force`)
- **Handled in**: existing `materialize()` logic — unchanged

### EC-4.2: `--repair` re-installs owned skills
- **Trigger**: `pathly-setup --repair --apply` after a core skill body update
- **Expected behavior**: Pathly-owned skill files overwritten with new content
- **Handled in**: existing `materialize(repair=True)` — no new code needed

---

## Known Limitations
- Copilot invocation prefix is `#pathly` placeholder — functional install but invocation may not work until Copilot prefix spec is confirmed
- Central manifest (`~/.pathly/manifest.json`) is out of scope; ownership tracked per-dest only
- "Remove non-Pathly skills?" prompt during `--apply` is out of scope (additive-only install)
