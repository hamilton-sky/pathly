# pathly

This is the canonical, tool-agnostic Pathly behavior for the pathly workflow.
Adapter skills should load and follow this prompt instead of duplicating workflow logic.

# Pathly

Use this workflow as the canonical front door for Pathly.

This core router works in host-neutral route names. Adapters decide how a user
invokes those routes in their environment.

## Parse `$ARGUMENTS`

Trim `$ARGUMENTS` and inspect the first word case-insensitively.

## Routes

### `help`

Run the Pathly help behavior from `core/prompts/help.md`.

When rendering help output, present route names unless the adapter has supplied
host-specific command formatting.

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

Run team-flow build entry for the feature: `team-flow <feature> build`.

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

Prefer the friendlier route aliases in new guidance:

- `flow <feature>` instead of `team-flow <feature>`
- `continue <feature>` instead of `build <feature>`
- `doctor [feature]` instead of `help --doctor [feature]`

### Anything else

Treat `$ARGUMENTS` as a plain-English request and run the director behavior from
`core/prompts/go.md`.

## Response Rule

Before invoking the selected behavior, print a short summary:

```text
Pathly route: <help|doctor|debug|explore|team-flow|review|director>
Reason: <one sentence>
```
