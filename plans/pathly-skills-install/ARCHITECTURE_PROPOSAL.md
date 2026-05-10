# pathly-skills-install — Architecture Proposal

## Problem Statement
`pathly-setup` installs agents but not skills. Skills (slash/at/hash commands) need
to be installed per-host using the same YAML-driven stitch pattern, so both surfaces
are set up in one command.

## Proposed Solution
Add `stitch_skill()` alongside `stitch_agent()`. Skill YAMLs live at
`adapters/<host>/_meta/<name>_skill.yaml` (the `_skill` suffix distinguishes them
from agent YAMLs in the same directory). Each adapter's `install.yaml` gains a
`skills:` section. `_run_host()` discovers skill YAMLs, stitches, and materializes
them after the existing agent pass.

## Architecture Diagram

```
install.yaml
  agents:  destination: ~/.claude/agents/
  skills:  destination: ~/.claude/
           structure: flat
       │
       ▼
_run_host()
  [agent pass]          [skill pass — NEW]
  glob *.yaml           glob *_skill.yaml
  stitch_agent()        stitch_skill()
  materialize()         materialize()
       │                       │
       ▼                       ▼
~/.claude/agents/      ~/.claude/
  architect.md           go.md
  builder.md             start.md
  ...                    end.md
                         help.md
                         pause.md
```

## Key Design Decisions

### Decision 1: Suffix-based YAML discovery (`*_skill.yaml`)
- **Options considered**: separate `skills/` subdirectory; `type: skill` field in YAML; `_skill` filename suffix
- **Chosen**: `_skill` suffix glob
- **Rationale**: no directory restructuring, no new required field, coexists cleanly with agent YAMLs in the same `_meta/` folder; suffix convention is self-documenting

### Decision 2: No frontmatter injection in skills
- **Options considered**: inject invocation as frontmatter (like agents inject name/model); plain body only
- **Chosen**: plain body, no injected frontmatter
- **Rationale**: Claude Code skill files are invoked by filename, not by frontmatter fields; Codex and Copilot equivalents also use plain markdown; injecting frontmatter would require each host to strip it at runtime

### Decision 3: wrapper replaces core body entirely
- **Options considered**: wrapper appended after core; wrapper as preamble; wrapper replaces entirely
- **Chosen**: wrapper replaces entirely
- **Rationale**: enables pure-alias skills (pause) with zero dependency on a core file; prevents platform-specific wrapper from being interleaved with generic core content; simpler to reason about

### Decision 4: Per-dest manifest, not central
- **Options considered**: central `~/.pathly/manifest.json`; per-dest `.pathly-manifest.json`
- **Chosen**: per-dest (same as agents)
- **Rationale**: reuses `materialize()` unchanged; avoids cross-host manifest coordination in this feature; central manifest is a separate, larger design decision

### Decision 5: warn-and-skip on missing core (no abort)
- **Options considered**: abort host install; raise exception; skip skill with warning
- **Chosen**: warn + skip
- **Rationale**: partial skill installs are better than broken agent installs; mirrors the existing `[warn] No core file for...` pattern in the agent pass

## Skill YAML Schema

```yaml
# Required
skill: go              # stem of core/skills/<name>.md to use as body source
invocation: /go        # platform-specific invocation prefix + command

# Optional
filename: go.md        # output filename (default: <yaml-stem-minus-_skill>.md)
strip_frontmatter: false  # strip leading ---...--- block from core body
wrapper: |             # replaces core body entirely (for aliases like pause)
  ...
natural_language: "go, continue, next step"  # hint for adapter tooling
```

## Risks
- **Copilot prefix unknown**: `invocation: "#pathly"` is a placeholder; installs correctly but may not invoke until spec is confirmed. Mitigated by TODO comment in all Copilot skill YAMLs.
- **skills: destination overlap with agents**: if a host uses the same dest for agents and skills (unlikely but possible), materialize() would share the manifest. Ownership tracking still works correctly — each filename is tracked independently.
