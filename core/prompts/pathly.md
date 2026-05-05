# pathly

This is the canonical, tool-agnostic Pathly behavior for the pathly workflow.
Adapter skills should load and follow this prompt instead of duplicating workflow logic.

# Pathly

Use this workflow as the canonical front door for Pathly.

For slash-command hosts, `/pathly` is canonical and `/path` is the supported
short alias. Do not tell Codex users to type Codex-conflicting commands like
`/help`; use `/pathly help` or `/path help` instead.

## Parse `$ARGUMENTS`

Trim `$ARGUMENTS` and inspect the first word case-insensitively.

## Routes

### `help`

Run the Pathly help behavior from `core/prompts/help.md`, without relying on the
literal `/help` command name.

When rendering portable help output, namespace user-facing commands under
`/pathly` and mention that `/path` is equivalent:

- `/help` -> `/pathly help`
- `/help --doctor [feature]` -> `/pathly doctor [feature]`
- `/go <request>` -> `/pathly <request>`
- `/team-flow <feature> ...` -> `/pathly flow <feature> ...`
- `/debug <symptom>` -> `/pathly debug <symptom>`
- `/explore <question>` -> `/pathly explore <question>`
- `/review` -> `/pathly review`
- `/build <feature>` -> `/pathly continue <feature>`

### `doctor`

Run doctor mode from `core/prompts/help.md` as if the user requested Pathly
doctor diagnostics.

### `debug <symptom>`

Run the debug workflow from `core/prompts/debug.md` using the remaining text as
the symptom.

### `explore <question>`

Run the explore workflow from `core/prompts/explore.md` using the remaining text
as the question.

### `flow <feature>` or `run <feature>`

Run the team-flow workflow from `core/prompts/team-flow.md` using the remaining
text as the feature and options.

### `continue <feature>`

Run team-flow build entry for the feature:

```text
team-flow <feature> build
```

### `review`

Run the review workflow from `core/prompts/review.md`.

### Direct skill routes

If the first word is one of these root skill names, run that skill with the
remaining text as its arguments:

- `archive` -> `core/prompts/archive.md`
- `bmad-import` -> `core/prompts/bmad-import.md`
- `build` -> `core/prompts/build.md`
- `go` -> `core/prompts/go.md`
- `lessons` -> `core/prompts/lessons.md`
- `plan` -> `core/prompts/plan.md`
- `prd-import` -> `core/prompts/prd-import.md`
- `retro` -> `core/prompts/retro.md`
- `storm` -> `core/prompts/storm.md`
- `team-flow` -> `core/prompts/team-flow.md`
- `verify-state` -> `core/prompts/verify-state.md`

Prefer the friendlier aliases in new guidance:

- `/pathly flow <feature>` instead of `/pathly team-flow <feature>`
- `/pathly continue <feature>` instead of `/pathly build <feature>`
- `/pathly doctor [feature]` instead of `/pathly help --doctor [feature]`

### Anything else

Treat `$ARGUMENTS` as a plain-English request and run the director behavior from
`core/prompts/go.md`.

## Response Rule

Before invoking the selected behavior, print a short summary:

```text
Pathly route: <help|doctor|debug|explore|team-flow|review|director>
Reason: <one sentence>
```
