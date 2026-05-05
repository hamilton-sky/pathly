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

The live Codex plugin reads `adapters/codex/skills/`. These wrappers are
Codex-safe: they load the same canonical `core/prompts/*.md` workflows but do
not include Claude-only model frontmatter such as `haiku`, `sonnet`, or `opus`.
Core model intent should stay portable as `simple`, `normal`, or `advanced`;
Codex wrappers can map those tiers to Codex-native models only when that is
explicitly supported.

Claude Code keeps its own model-specific wrappers under
`adapters/claude-code/skills/` for the Claude plugin package.
