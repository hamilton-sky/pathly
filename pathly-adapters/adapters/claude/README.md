# Claude Code Adapter

Claude Code should expose the cross-framework Pathly entry points:

```text
/pathly ...
/path ...
```

`/pathly` is canonical. `/path` is the short alias for daily use.

Claude Code can keep the existing command names for backwards compatibility:

```text
/go
/help
/debug
/explore
/team-flow
```

When docs or generated help describe the portable Pathly command surface, prefer
`/pathly` examples and mention that `/path` is equivalent.

Skills are loaded directly from `core/skills/` — no adapter wrappers needed.
`adapters/claude/agents/` provides Claude Code-specific agent files with
`tools:[]` frontmatter and `Agent()` invocation syntax for subagent spawning.

Current status: `core/skills/`, `adapters/claude/agents/`, `install.sh`, and
`install.ps1` provide the working Claude Code install path.
