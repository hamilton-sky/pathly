# pathly - Universal Entry Point

`pathly` is the tool-agnostic front door for Pathly.

It accepts a short command or a plain-English request and routes to the lightest
safe workflow.

For slash-command adapters, `/pathly` is the canonical Pathly command and
`/path` is the supported short alias. Both commands must route to this same
entry point. Legacy framework commands can remain as compatibility aliases, but
new cross-framework docs should lead with `/pathly` and mention `/path` for
daily use.

## Inputs

- Optional command word: `help`, `doctor`, `debug`, `explore`, `flow`, `run`,
  `continue`, `review`, or any root skill name such as `plan`, `build`,
  `archive`, `lessons`, `prd-import`, `bmad-import`, `retro`, `storm`,
  `team-flow`, or `verify-state`
- Optional free text request
- Current project files, especially `plans/`, `debugs/`, and git status

## Routing

Use this order:

1. `help` with no other request: show Pathly help, not host-tool help.
2. `doctor`: diagnose Pathly state, stale feedback, missing files, and local
   prerequisites.
3. `debug <symptom>`: route to the debug workflow.
4. `explore <question>`: route to the read-only exploration workflow.
5. `flow <feature>` or `run <feature>`: route to the team-flow workflow.
6. `review`: review current code changes.
7. Any root skill name: route to that skill with the remaining text.
8. Any other text: treat as a plain-English request and route through the
   director workflow.

## Examples

```text
pathly help
pathly doctor
pathly add password reset
pathly debug checkout button does nothing
pathly explore how auth state flows
pathly flow checkout-flow
pathly continue checkout-flow
```

Slash-command adapters should expose the same examples as:

```text
/pathly help
/pathly doctor
/pathly add password reset
/pathly debug checkout button does nothing
/pathly explore how auth state flows
/pathly flow checkout-flow
/pathly continue checkout-flow
/pathly plan checkout-flow standard
/pathly verify-state checkout-flow
```

The short alias is equivalent:

```text
/path help
/path add password reset
```

## Adapter Notes

- Slash-command adapters expose this as `/pathly ...` and `/path ...`.
- Codex uses `/pathly help` or `/path help` to avoid its built-in `/help`.
- Claude Code should support `/pathly ...` and `/path ...`; it may also keep
  `/go`, `/help`, `/debug`, and `/explore` for backwards compatibility.
- CLI exposes this through `pathly ...` commands where practical.
