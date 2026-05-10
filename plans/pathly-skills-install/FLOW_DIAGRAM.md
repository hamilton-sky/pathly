# pathly-skills-install — Flow Diagram

## Happy Path: pathly-setup --apply (claude)

```
pathly-setup --apply
        │
        ▼
detect_hosts() → ["claude"]
        │
        ▼
_run_host("claude")
        │
        ├─── AGENT PASS (unchanged) ──────────────────────┐
        │    glob _meta/*.yaml (excl install.yaml,         │
        │         *_skill.yaml)                            │
        │    stitch_agent(core, meta) × 12                 │
        │    materialize() → ~/.claude/agents/             │
        │                                                  │
        ├─── SKILL PASS (new) ────────────────────────────┤
        │    read install_cfg["skills"]                    │
        │    dest = ~/.claude/                             │
        │    glob _meta/*_skill.yaml                       │
        │          │                                       │
        │          ├─ go_skill.yaml                        │
        │          │   stitch_skill(core/skills/go.md, …)  │
        │          │   → go.md content                     │
        │          ├─ start_skill.yaml                     │
        │          │   stitch_skill(…/start.md, …)         │
        │          │   → start.md content                  │
        │          ├─ end_skill.yaml → end.md content      │
        │          ├─ help_skill.yaml → help.md content    │
        │          └─ pause_skill.yaml                     │
        │              wrapper set → use wrapper body      │
        │              → pause.md content                  │
        │                                                  │
        │    materialize(skill_files, ~/.claude/)          │
        │    → writes go.md, start.md, end.md,             │
        │      help.md, pause.md                           │
        │    → updates ~/.claude/.pathly-manifest.json     │
        │                                                  │
        └─── print summary ───────────────────────────────┘
             [claude] Wrote 12 agent(s) to ~/.claude/agents/
             [claude] Wrote 5 skill(s) to ~/.claude/
```

## stitch_skill() Internal Flow

```
stitch_skill(core_path, meta_path)
        │
        ├─ load YAML from meta_path
        │   malformed → ValueError
        │   missing required fields → ValueError
        │
        ├─ wrapper set?
        │   YES → body = wrapper; skip core read
        │   NO  → core_path.exists()?
        │           NO  → FileNotFoundError
        │           YES → body = core_path.read_text()
        │
        ├─ strip_frontmatter: true?
        │   YES → remove leading ---...--- block from body
        │   NO  → body unchanged
        │
        └─ return body (plain markdown, no frontmatter injected)
```

## Fallback: skill core file missing (no wrapper)

```
_run_host() skill loop
        │
        ├─ stitch_skill(core_path, meta_path)
        │   core_path missing, no wrapper
        │   → raises FileNotFoundError
        │
        └─ except FileNotFoundError:
               print "[warn] No core skill for 'x', skipping"
               continue  ← next skill YAML
```

## Component Legend

| Symbol | Meaning |
|--------|---------|
| _run_host() | Per-host install orchestrator in setup_command.py |
| stitch_skill() | Assembles skill body from core .md + adapter YAML |
| materialize() | Writes files to dest, tracks ownership in .pathly-manifest.json |
| *_skill.yaml | Adapter-specific skill metadata in adapters/<host>/_meta/ |
| core/skills/*.md | Platform-agnostic skill body text |
