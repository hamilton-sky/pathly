# CLI Adapter

The CLI adapter exposes Pathly through the terminal command:

```text
pathly
```

Current command contract:

```text
pathly init <feature>
pathly help [feature]
pathly go <plain English request>
pathly flow <feature>
pathly run <feature>
pathly team-flow <feature>
pathly debug <symptom>
pathly explore <question>
pathly review
pathly doctor
pathly install codex
pathly install claude
```

These commands expose the same user-facing Pathly workflows that slash-command
hosts expose through `/pathly ...`. `pathly help`, `pathly go`, `pathly debug`,
`pathly explore`, and `pathly review` are especially important fallbacks for
hosts such as Codex that may interpret "Use Pathly help" as a terminal command
instead of invoking the plugin skill.

Future work: align `pathly <plain English request>` with the universal
`core/prompts/pathly.md` router.

The CLI adapter should stay a terminal-facing wrapper. Shared routing language,
workflow semantics, and template definitions belong in `core/`; Python command
implementation belongs in the repo-root `pathly/` package.
