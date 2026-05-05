---
name: pathly
description: Codex-safe Pathly entry point. Route /pathly help, doctor, debug, explore, flow, review, continue, or plain-English requests to the right Pathly workflow without using Codex built-in /help.
argument-hint: "[help|doctor|debug|explore|flow|review|continue|plain English request]"
---

# Pathly

Use this skill as the Codex-safe front door for Pathly.

Do not tell the user to type Codex-conflicting commands like `/help`. In Codex,
Pathly commands should be namespaced under `/pathly`.

## Parse `$ARGUMENTS`

Trim `$ARGUMENTS` and inspect the first word case-insensitively.

## Routes

### `help`

Run the Pathly help behavior from `skills/help/SKILL.md`, without relying on the
literal `/help` command name.

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

### Anything else

Treat `$ARGUMENTS` as a plain-English request and run the director behavior from
`skills/go/SKILL.md`.

## Response Rule

Before invoking the selected behavior, print a short summary:

```text
Pathly route: <help|doctor|debug|explore|team-flow|review|director>
Reason: <one sentence>
```
