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

This adapter owns the Claude-facing skill wrappers under
`adapters/claude-code/skills/`. Those wrappers load the canonical workflows from
`core/prompts/` while preserving Claude Code slash-command metadata.

Current status: `adapters/claude-code/skills/`,
`adapters/claude-code/agents/`, `install.sh`, and `install.ps1` provide the
working Claude Code install path.
