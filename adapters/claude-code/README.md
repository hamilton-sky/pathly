# Claude Code Adapter

Claude Code can keep the existing command names for backwards compatibility:

```text
/go
/help
/debug
/explore
/team-flow
```

This adapter should eventually generate Claude Code skill files from
`core/prompts/` and Claude agent files from `core/agents/`.

Current status: the root `skills/`, `agents/`, `install.sh`, and `install.ps1`
still provide the working Claude Code install path.
