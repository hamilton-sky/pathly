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

This adapter should eventually generate Claude Code skill files from
`core/prompts/` and Claude agent files from `core/agents/`.

Current status: the root `skills/`, `agents/`, `install.sh`, and `install.ps1`
still provide the working Claude Code install path.
