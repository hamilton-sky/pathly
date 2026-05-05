# CLI Adapter

The CLI adapter exposes Pathly through the terminal command:

```text
pathly
```

Current command contract:

```text
pathly init <feature>
pathly run <feature>
pathly team-flow <feature>
pathly doctor
pathly install codex
pathly install claude
```

Future work: align `pathly <plain English request>` with the universal
`core/prompts/pathly.md` router.

The CLI adapter should stay a terminal-facing wrapper. Shared routing language,
workflow semantics, and template definitions belong in `core/`; Python command
implementation belongs in the repo-root `pathly/` package.
