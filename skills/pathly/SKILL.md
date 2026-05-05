---
name: pathly
description: Pathly entry point. Route /pathly or /path help, doctor, debug, explore, flow, review, continue, plan, build, archive, lessons, imports, verify-state, or plain-English requests to the right Pathly workflow.
argument-hint: "[help|doctor|debug|explore|flow|review|continue|plan|build|archive|lessons|verify-state|plain English request]"
---

# Pathly

Use this skill as the canonical front door for Pathly.

For slash-command hosts, `/pathly` is canonical and `/path` is the supported
short alias. Do not tell Codex users to type Codex-conflicting commands like
`/help`; use `/pathly help` or `/path help` instead.

## Parse `$ARGUMENTS`

Trim `$ARGUMENTS` and inspect the first word case-insensitively.

## Routes

### `help`

Run the Pathly help behavior from `skills/help/SKILL.md`, without relying on the
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

Run doctor mode from `skills/help/SKILL.md` as if the user requested Pathly
doctor diagnostics.

### `debug <symptom>`

Run the debug workflow from `skills/debug/SKILL.md` using the remaining text as
the symptom.

### `explore <question>`

Run the explore workflow from `skills/explore/SKILL.md` using the remaining text
as the question.

### `flow <feature>` or `run <feature>`

Run the team-flow workflow from `skills/team-flow/SKILL.md` using the remaining
text as the feature and options.

### `continue <feature>`

Run team-flow build entry for the feature:

```text
team-flow <feature> build
```

### `review`

Run the review workflow from `skills/review/SKILL.md`.

### Direct skill routes

If the first word is one of these root skill names, run that skill with the
remaining text as its arguments:

- `archive` -> `skills/archive/SKILL.md`
- `bmad-import` -> `skills/bmad-import/SKILL.md`
- `build` -> `skills/build/SKILL.md`
- `go` -> `skills/go/SKILL.md`
- `lessons` -> `skills/lessons/SKILL.md`
- `plan` -> `skills/plan/SKILL.md`
- `prd-import` -> `skills/prd-import/SKILL.md`
- `retro` -> `skills/retro/SKILL.md`
- `storm` -> `skills/storm/SKILL.md`
- `team-flow` -> `skills/team-flow/SKILL.md`
- `verify-state` -> `skills/verify-state/SKILL.md`

Prefer the friendlier aliases in new guidance:

- `/pathly flow <feature>` instead of `/pathly team-flow <feature>`
- `/pathly continue <feature>` instead of `/pathly build <feature>`
- `/pathly doctor [feature]` instead of `/pathly help --doctor [feature]`

### Anything else

Treat `$ARGUMENTS` as a plain-English request and run the director behavior from
`skills/go/SKILL.md`.

## Response Rule

Before invoking the selected behavior, print a short summary:

```text
Pathly route: <help|doctor|debug|explore|team-flow|review|director>
Reason: <one sentence>
```
