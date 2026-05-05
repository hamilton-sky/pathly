# Codex Adapter

Codex exposes Pathly as plugin skills, not as custom slash commands in current
Codex builds. Do not document `/pathly` as a Codex command unless a future Codex
release supports plugin-defined slash commands.

Use natural-language skill prompts:

```text
Use Pathly help
Use Pathly doctor on this project
Use Pathly to add password reset
Use Pathly to debug checkout button does nothing
Use Pathly to explore how auth state flows
Use Pathly flow for checkout-flow
```

Codex reserves slash commands such as `/help` for its own UI. If a user types
`/pathly`, current Codex versions may report it as an unrecognized command.

Recommended CLI fallback from inside a Codex workspace:

```text
pathly doctor
pathly init <feature>
pathly run <feature>
```

Current status: the live Codex plugin still reads `skills/` from the repository
root. The `pathly` skill wrapper lives at `skills/pathly/SKILL.md`, and the
short alias wrapper lives at `skills/path/SKILL.md`, until the adapter generator
exists.
